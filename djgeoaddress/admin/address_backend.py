"""Admin for virtual address backend diagnostics."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib import admin, messages
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..models.address_backend import AddressBackendInfo, AddressBackendInfoQuerySet
from ..models.address_lookup import AddressLookup, AddressLookupQuerySet
from .utils import (
    find_object_by_identifier,
    get_object_with_identifier,
    render_settings_row,
)

try:
    from geoaddress.helpers import (
        get_address_backends_from_config as get_address_backends_fn,
        get_address_by_reference as get_address_by_reference_fn,
        search_addresses as search_addresses_fn,
    )
except ImportError:
    search_addresses_fn = None
    get_address_backends_fn = None
    get_address_by_reference_fn = None


def get_backend_configs() -> list[Dict[str, Any]]:
    config = getattr(settings, "GEOADDRESS_BACKENDS", None)
    return list(config or [])


def get_backend_config_for_path(class_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not class_path:
        return None
    for backend in get_backend_configs():
        if backend.get("class") == class_path:
            return backend
    return None


def _parse_address_term(term: str) -> Dict[str, Optional[str]]:
    """Parse an address string to extract components.

    Tries to extract postal_code (5 digits) and city from the term.
    """
    import re

    term = term.strip()
    if not term:
        return {"address_line1": term, "postal_code": None, "city": None}

    postal_code_pattern = r"\b(\d{5})\b"
    postal_match = re.search(postal_code_pattern, term)

    postal_code = None
    city = None
    address_line1 = term

    if postal_match:
        postal_code = postal_match.group(1)
        postal_pos = postal_match.start()

        parts = term.split(postal_code)
        if len(parts) >= 2:
            address_line1 = parts[0].strip()
            city_part = parts[1].strip()
            if city_part:
                city = city_part
        else:
            address_line1 = term[:postal_pos].strip()

    return {
        "address_line1": address_line1,
        "postal_code": postal_code,
        "city": city,
    }


def build_address_suggestions(
    config_list: list[Dict[str, Any]], term: str, backend: Optional[str] = None
) -> list[Dict[str, Any]]:
    if not config_list or not term or search_addresses_fn is None:
        return []

    try:
        search_result = search_addresses_fn(
            backends_config=config_list,
            query=term,
            min_confidence=0.0,
            limit=20,
            backend=backend,
        )
    except Exception as exc:  # pragma: no cover - defensive
        error_detail = str(exc)
        # Include backend name in error if specified
        if backend:
            error_detail = f"[Backend: {backend}] {error_detail}"
        return [
            {
                "label": f"Error: {error_detail}",
                "raw": {"error": error_detail, "errors": [str(exc)], "backend": backend},
            }
        ]

    if search_result.get("error"):
        error_msg = search_result.get("error", "Unknown error")
        errors_list = search_result.get("errors", [])
        if errors_list:
            error_msg = "; ".join(str(e) for e in errors_list[:3])
        # Include backend name in error message if specified
        if backend:
            error_msg = f"[Backend: {backend}] {error_msg}"
        # Return error as a suggestion so it's visible in admin
        return [{"label": f"Error: {error_msg}", "raw": {**search_result, "backend": backend}}]

    backend_name = search_result.get("backend_used") or ""
    results = search_result.get("results", [])

    if not results:
        return [{"label": "No result from backends", "raw": {"error": "No result"}}]

    rows = []
    for result in results:
        raw = dict(result or {})
        if backend_name and not raw.get("backend_used"):
            raw["backend_used"] = backend_name
        backend_reference = (
            raw.get("backend_reference")
            or raw.get("address_reference")
            or search_result.get("backend_reference")
            or ""
        )
        if backend_reference and not raw.get("backend_reference"):
            raw["backend_reference"] = backend_reference
        label = raw.get("formatted_address") or raw.get("normalized_address") or term
        label = _clean_address_label(label)
        rows.append({"label": label, "raw": raw})

    return rows


def _clean_address_label(label: str) -> str:
    """Remove warnings and low-level messages from address labels."""
    if not label:
        return label

    import re

    label = str(label).strip()

    patterns_to_remove = [
        r"\s*\([^)]*Low importance match[^)]*\)",
        r"\s*\([^)]*Low confidence match[^)]*\)",
        r"\s*\([^)]*Low importance[^)]*\)",
        r"\s*\([^)]*Low confidence[^)]*\)",
    ]

    for pattern in patterns_to_remove:
        label = re.sub(pattern, "", label, flags=re.IGNORECASE)

    return label.strip()


@admin.register(AddressBackendInfo)
class AddressBackendInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/djgeoaddress/change_list.html"
    ordering = ["name"]
    actions = None
    list_display = [
        "display_name_column",
        "status_display",
        "documentation_link",
        "site_link",
    ]

    change_form_template = "admin/djgeoaddress/change_form.html"
    search_fields = ["name", "class_path", "status"]
    readonly_fields = [
        "name",
        "class_path",
        "status_display",
        "documentation_link",
        "site_link",
        "packages_display",
        "config_display_detail",
        "error_display",
    ]

    def get_queryset(self, request):
        qs = AddressBackendInfo.objects.all()
        return qs

    def get_actions(self, request):
        """Disable bulk actions/selection like Provider admin."""
        return {}

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
        term = search_term.strip().lower()
        if not term:
            return queryset, False

        def _matches(obj: AddressBackendInfo) -> bool:
            candidates = [
                obj.display_name,
                obj.name,
                obj.class_path,
                obj.status,
            ]
            diag = obj.diagnostic
            candidates.append(str(diag.get("backend_name", "")))
            candidates.append(str(diag.get("backend_display_name", "")))
            candidates.append(str(diag.get("class", "")))
            return any(value and term in str(value).lower() for value in candidates)

        filtered = [obj for obj in queryset if _matches(obj)]
        return AddressBackendInfoQuerySet(model=self.model, data=filtered), False

    def has_add_permission(self, request):
        return False

    def get_object(self, request, object_id, from_field=None):
        """Récupère l'objet address backend par son name (qui est maintenant le pk)."""
        return get_object_with_identifier(self, request, object_id, from_field)

    # Helpers ----------------------------------------------------------
    def _all_backend_configs(self):
        return get_backend_configs()

    def _get_backend_config_for_path(self, class_path: str | None):
        return get_backend_config_for_path(class_path)

    def _get_backend_info(self, backend_name: str):
        """Récupère le backend par son name."""
        try:
            queryset = self.get_queryset(None)
            try:
                return queryset.get(pk=backend_name)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return find_object_by_identifier(queryset, backend_name)
        except Exception:
            return None

    def _build_results(self, config_list, term):
        return build_address_suggestions(config_list, term)

    # List display helpers ---------------------------------------------
    @admin.display(description=_("Backend"))
    def display_name_column(self, obj: AddressBackendInfo):
        return obj.display_name

    @admin.display(description=_("Status"))
    def status_display(self, obj: AddressBackendInfo):
        status = (obj.status or "").lower()
        if status == "working":
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0f5132; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">✅ {}</span>',
                _("Working"),
            )
        if status == "ready":
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0a3622; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">✅ {}</span>',
                _("Ready"),
            )
        if status == "missing_config":
            return format_html(
                '<span style="background-color: #fff3cd; color: #664d03; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">⚠️ {}</span>',
                _("Config Required"),
            )
        if status == "missing_packages":
            return format_html(
                '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ {}</span>',
                _("Packages Missing"),
            )
        return format_html(
            '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
            'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ {}</span>',
            _("Unavailable"),
        )

    @admin.display(description=_("Selected"))
    def selected_display(self, obj: AddressBackendInfo):
        return _("Yes") if obj.is_selected else _("No")

    @admin.display(description=_("Documentation"))
    def documentation_link(self, obj: AddressBackendInfo):
        if not obj.documentation_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.documentation_url,
            obj.documentation_url,
        )

    @admin.display(description=_("Website"))
    def site_link(self, obj: AddressBackendInfo):
        if not obj.site_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.site_url,
            obj.site_url,
        )

    # Readonly details -------------------------------------------------
    @admin.display(description=_("Packages"))
    def packages_display(self, obj: AddressBackendInfo):
        packages = obj.packages_summary
        if not packages:
            return "—"
        rows = []
        for name, installed in packages:
            icon = "✓" if installed else "✗"
            color = "#198754" if installed else "#dc3545"
            rows.append((color, icon, name))
        return format_html_join(
            "<br>",
            '<span style="color:{};">{}</span> <code>{}</code>',
            rows,
        )

    @admin.display(description=_("Configuration"))
    def config_display(self, obj: AddressBackendInfo):
        """Simple config display for list view."""
        entries = obj.config_summary
        if not entries:
            return "—"
        configured = sum(1 for _, present, _ in entries if present)
        total = len(entries)
        if configured == total:
            return format_html('<span style="color: #198754;">✓ {} configured</span>', total)
        return format_html(
            '<span style="color: #dc3545;">✗ {} / {} configured</span>',
            configured,
            total,
        )

    @admin.display(description=_("Configuration Variables"))
    def config_display_detail(self, obj: AddressBackendInfo):
        """Displays all config variables in edit page with table."""
        entries = obj.config_summary
        if not entries:
            return mark_safe(
                '<p style="color: #666;">No specific configuration required for this backend.</p>'
            )

        # Keys that are not sensitive (public URLs, user agents, etc.)
        non_sensitive_keys = {
            "NOMINATIM_BASE_URL",
            "NOMINATIM_USER_AGENT",
            "PHOTON_BASE_URL",
        }

        backend_config = self._get_backend_config_for_path(obj.class_path)
        config_dict = backend_config.get("config", {}) if backend_config else {}

        rows = []
        for key, present, preview in entries:
            # Get actual value from config
            actual_value = config_dict.get(key)

            # Check if value is actually set (not None, not empty string)
            is_configured = present and actual_value is not None and str(actual_value).strip() != ""

            if is_configured:
                icon = mark_safe('<span style="color: #198754; font-weight: bold;">✓</span>')
                status_text = mark_safe('<span style="color: #198754;">Configured</span>')

                if key in non_sensitive_keys:
                    # For non-sensitive keys, show full value directly
                    value_html = format_html("<code>{}</code>", str(actual_value))
                else:
                    # For sensitive keys, show masked value with eye button
                    value_html = format_html(
                        '<span class="config-eye" data-var="{}" style="cursor: pointer; color: #6c757d; margin-right: 8px;" '
                        'title="Click to show/hide">👁️</span>'
                        '<span class="config-value-masked" data-var="{}" style="color: #6c757d;">••••••••</span>'
                        '<span class="config-value-revealed" data-var="{}" style="display: none;"><code>{}</code></span>',
                        key,
                        key,
                        key,
                        str(actual_value),
                    )
            else:
                icon = mark_safe('<span style="color: #dc3545; font-weight: bold;">✗</span>')
                status_text = mark_safe('<span style="color: #dc3545;">Missing</span>')
                value_html = mark_safe('<code style="color: #6c757d;">Not defined</code>')

            rows.append(render_settings_row(icon, key, status_text, value_html))

        table_html = format_html(
            """
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6; width: 30px;"></th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Variable</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Status</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Value</th>
                </tr>
            </thead>
            <tbody>
                {}
            </tbody>
        </table>
        <p style="margin-top: 15px; padding: 10px; background-color: #cfe2ff; border-left: 4px solid #0d6efd; color: #084298;">
            <strong>💡 To configure:</strong> Edit the <code>GEOADDRESS_BACKENDS</code> setting in your Django settings file.
        </p>
        """,
            mark_safe("".join(str(row) for row in rows)),  # nosec
        )

        return table_html

    @admin.display(description=_("Error"))
    def error_display(self, obj: AddressBackendInfo):
        return obj.error or "—"


class BackendFilter(admin.SimpleListFilter):
    """Filter to select a backend for address search."""

    title = _("Backend")
    parameter_name = "backend"

    def lookups(self, request, model_admin):
        """Return a list of available backends."""
        backends = AddressBackendInfo.objects.all()
        choices = [("", _("All backends"))]
        for backend in backends:
            display_name = backend.display_name or backend.name
            # Get the actual backend name from diagnostic if available, otherwise use name
            diagnostic = getattr(backend, "_diagnostic", {})
            backend_name = diagnostic.get("backend_name") or backend.name
            # Use the backend name (like "nominatim", "google_maps") as the value
            choices.append((backend_name, display_name))
        return choices

    def queryset(self, request, queryset):
        # This filter doesn't actually filter the queryset
        # Instead, the backend parameter is used in get_queryset to force a backend
        return queryset


@admin.register(AddressLookup)
class AddressLookupAdmin(admin.ModelAdmin):
    list_display = [
        "reference_link",
        "address_line1_display",
        "address_line2_display",
        "address_line3_display",
        "city_display",
        "postal_code_display",
        "state_display",
        "country_display",
        "latitude_display",
        "longitude_display",
        "confidence_display",
        "backend_used_display",
    ]
    search_fields = ["label", "backend_used", "backend_reference"]
    ordering = ["label"]
    list_per_page = 20
    list_display_links = ("reference_link",)
    change_list_template = "admin/change_list.html"
    list_filter = [BackendFilter]
    readonly_fields = [
        "reference_slug_display",
        "label",
        "backend_used",
        "backend_used_display",
        "backend_reference",
        "confidence_display",
        "address_line1_display",
        "address_line2_display",
        "address_line3_display",
        "city_display",
        "postal_code_display",
        "state_display",
        "country_display",
        "latitude_display",
        "longitude_display",
        "raw_payload_full_display",
    ]
    fieldsets = (
        (
            _("Summary"),
            {
                "fields": (
                    "reference_slug_display",
                    "label",
                    "backend_used_display",
                    "backend_reference",
                    "confidence_display",
                )
            },
        ),
        (
            _("Address components"),
            {
                "fields": (
                    "address_line1_display",
                    "address_line2_display",
                    "address_line3_display",
                    "city_display",
                    "postal_code_display",
                    "state_display",
                    "country_display",
                )
            },
        ),
        (
            _("Geolocation"),
            {
                "fields": (
                    "latitude_display",
                    "longitude_display",
                )
            },
        ),
        (
            _("Raw payload"),
            {
                "fields": ("raw_payload_full_display",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if request is None:
            return False
        return request.method in ("GET", "HEAD")

    _REFERENCE_SAFE_CHARS = "._~:@"
    _SLUG_SEPARATOR = "-"
    _CACHE_TIMEOUT = 900  # 15 minutes

    def get_queryset(self, request):
        query = (request.GET.get("q") or "").strip()
        # Get backend name from filter parameter (e.g., "nominatim", "google_maps")
        backend_name = (request.GET.get("backend") or "").strip()

        # Use all backends config for search_addresses
        # The backend parameter will be passed to force a specific backend
        configs = get_backend_configs()

        data = []
        if configs and query:
            # Pass backend_name to build_address_suggestions which will use it in search_addresses
            for entry in build_address_suggestions(
                configs, query, backend=backend_name if backend_name else None
            ):
                raw = entry.get("raw") or {}
                obj = AddressLookup(
                    label=entry.get("label") or "",
                    backend_used=raw.get("backend_used") or raw.get("backend") or "",
                    backend_reference=(
                        raw.get("backend_reference") or raw.get("address_reference") or ""
                    ),
                    raw_payload=raw,
                )
                slug_value = self._build_reference_slug(obj.backend_used, obj.backend_reference)
                if slug_value:
                    obj._lookup_slug = slug_value
                    obj.pk = slug_value
                    self._cache_payload(slug_value, raw, obj.backend_used)
                data.append(obj)

        return AddressLookupQuerySet(model=AddressLookup, data=data)

    # Helpers -------------------------------------------------------------
    def _build_reference_slug(
        self, backend_name: Optional[str], backend_reference: Optional[str]
    ) -> Optional[str]:
        if not backend_reference:
            return None
        backend_identifier = self._normalize_backend_identifier(backend_name)
        if not backend_identifier:
            return None
        backend_token = quote(backend_identifier, safe=self._REFERENCE_SAFE_CHARS)
        reference_token = quote(str(backend_reference), safe=self._REFERENCE_SAFE_CHARS)
        return f"{backend_token}{self._SLUG_SEPARATOR}{reference_token}"

    def _get_obj_slug(self, obj: AddressLookup) -> Optional[str]:
        slug_value = getattr(obj, "_lookup_slug", None)
        if slug_value:
            return slug_value  # type: ignore[no-any-return]
        slug_value = self._build_reference_slug(obj.backend_used, obj.backend_reference)
        if slug_value:
            obj._lookup_slug = slug_value  # type: ignore[attr-defined]
        return slug_value

    @staticmethod
    def _normalize_backend_identifier(value: Optional[str]) -> str:
        if not value:
            return ""
        cleaned = str(value).strip()
        if not cleaned:
            return ""
        return cleaned

    def _parse_slug(self, slug_value: str) -> tuple[Optional[str], Optional[str]]:
        if not slug_value or self._SLUG_SEPARATOR not in slug_value:
            return None, None
        backend_token, reference_token = slug_value.split(self._SLUG_SEPARATOR, 1)
        backend_name = unquote(backend_token).strip()
        reference = unquote(reference_token).strip()
        return backend_name or None, reference or None

    def _cache_key(self, slug_value: str) -> str:
        return f"geoaddress:addresslookup:{slug_value}"

    def _cache_payload(self, slug_value: Optional[str], payload: Dict[str, Any], backend_label: str):
        if not slug_value or not payload:
            return
        cache.set(
            self._cache_key(slug_value),
            {
                "payload": payload,
                "backend_label": backend_label,
            },
            timeout=self._CACHE_TIMEOUT,
        )

    def _fetch_backend_payload(
        self,
        backend_name: Optional[str],
        backend_reference: Optional[str],
        *,
        slug_value: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        if not backend_reference:
            return {"error": "Missing backend reference.", "backend_reference": ""}, ""
        backend_identifier = self._normalize_backend_identifier(backend_name)
        if not backend_identifier:
            return (
                {
                    "error": "Missing backend identifier.",
                    "backend_reference": backend_reference,
                },
                "",
            )
        cache_slug = slug_value or self._build_reference_slug(backend_identifier, backend_reference)
        if cache_slug:
            cached_entry = cache.get(self._cache_key(cache_slug))
            if cached_entry:
                payload = dict(cached_entry.get("payload") or {})
                backend_label = cached_entry.get("backend_label") or backend_identifier
                payload.setdefault("backend_reference", backend_reference)
                payload.setdefault("backend_used", backend_identifier)
                return payload, backend_label

        if pm_get_address_by_reference is None:
            return (
                {
                    "error": "python-missive helpers are not available.",
                    "backend_reference": backend_reference,
                },
                backend_identifier,
            )
        configs = get_backend_configs()
        if not configs:
            return (
                {
                    "error": "No address backends configured.",
                    "backend_reference": backend_reference,
                },
                backend_identifier,
            )
        payload = get_address_by_reference_fn(
            configs,
            backend=backend_identifier,
            address_reference=backend_reference,
        )
        backend_label = payload.get("backend_used") or backend_identifier
        if cache_slug:
            self._cache_payload(cache_slug, payload, backend_label)
        return payload, backend_label

    @staticmethod
    def _derive_label_from_payload(payload: Optional[Dict[str, Any]]) -> str:
        if not payload:
            return ""
        for key in ("formatted_address", "label"):
            value = payload.get(key)
            if value:
                return str(value)
        normalized = payload.get("normalized_address") or {}
        for key in ("formatted_address", "label"):
            value = normalized.get(key)
            if value:
                return str(value)
        return ""

    @admin.display(description=_("Reference"))
    def reference_link(self, obj: AddressLookup):
        slug_value = self._get_obj_slug(obj)
        reference = obj.backend_reference or "—"
        if not slug_value:
            return reference
        try:
            url = reverse("admin:djgeoaddress_addresslookup_change", args=[slug_value])
        except Exception:
            return reference
        return format_html('<a href="{}">{}</a>', url, reference)

    @admin.display(description=_("Detail slug"))
    def reference_slug_display(self, obj: AddressLookup):
        return self._get_obj_slug(obj) or "—"

    def _make_lookup_object(
        self,
        *,
        payload: Dict[str, Any],
        backend_label: str,
        backend_reference: str,
        slug_value: str,
    ) -> AddressLookup:
        obj = AddressLookup(
            label=self._derive_label_from_payload(payload)
            or backend_reference
            or backend_label,
            backend_used=backend_label,
            backend_reference=backend_reference,
            raw_payload=payload,
        )
        obj.pk = slug_value
        obj._lookup_slug = slug_value  # type: ignore[attr-defined]
        return obj

    def get_object(self, request, object_id, from_field=None):
        backend_name, backend_reference = self._parse_slug(object_id)
        if not backend_name or not backend_reference:
            messages.error(request, _("Unable to open detail view for this reference."))
            return None
        payload, backend_label = self._fetch_backend_payload(
            backend_name, backend_reference, slug_value=object_id
        )
        if "error" in payload:
            messages.warning(
                request,
                _("Backend response contains an error: %(error)s")
                % {"error": payload.get("error")},
            )
        return self._make_lookup_object(
            payload=payload,
            backend_label=backend_label or backend_name or "",
            backend_reference=backend_reference,
            slug_value=object_id,
        )

    @admin.display(description=_("Raw payload"))
    def raw_payload_full_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="white-space: pre-wrap; max-width: 640px;">{}</pre>',
            payload,
        )

    def _get_from_payload(self, obj: AddressLookup, *keys: str) -> Optional[str]:
        """Extract value from raw_payload using multiple possible keys."""
        if not obj.raw_payload:
            return None
        payload = obj.raw_payload
        normalized = payload.get("normalized_address") or {}
        for key in keys:
            value = payload.get(key) or normalized.get(key)
            if value:
                return str(value)
        return None

    @admin.display(description=_("Address Line 1"))
    def address_line1_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "address_line1", "line1")
        return value or "—"

    @admin.display(description=_("Address Line 2"))
    def address_line2_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "address_line2", "line2")
        return value or "—"

    @admin.display(description=_("Address Line 3"))
    def address_line3_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "address_line3", "line3")
        return value or "—"

    @admin.display(description=_("City"))
    def city_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "city")
        return value or "—"

    @admin.display(description=_("Postal Code"))
    def postal_code_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "postal_code", "postal_code")
        return value or "—"

    @admin.display(description=_("State"))
    def state_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "state")
        return value or "—"

    @admin.display(description=_("Country"))
    def country_display(self, obj: AddressLookup):
        value = self._get_from_payload(obj, "country")
        return value or "—"

    @admin.display(description=_("Latitude"))
    def latitude_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = obj.raw_payload
        normalized = payload.get("normalized_address") or {}
        lat = payload.get("latitude") or normalized.get("latitude")
        if lat is not None:
            try:
                lat_val = float(lat)
                return f"{lat_val:.6f}"
            except (TypeError, ValueError):
                return "—"
        return "—"

    @admin.display(description=_("Longitude"))
    def longitude_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = obj.raw_payload
        normalized = payload.get("normalized_address") or {}
        lon = payload.get("longitude") or normalized.get("longitude")
        if lon is not None:
            try:
                lon_val = float(lon)
                return f"{lon_val:.6f}"
            except (TypeError, ValueError):
                return "—"
        return "—"

    @admin.display(description=_("Backend"))
    def backend_used_display(self, obj: AddressLookup):
        """Display backend name with proper formatting."""
        backend_name = obj.backend_used or ""
        if not backend_name:
            return "—"

        # Try to get display name from backend configuration
        try:
            configs = getattr(settings, "GEOADDRESS_BACKENDS", [])
            backends = get_address_backends_fn(configs) if get_address_backends_fn else []

            # Normalize backend_name for comparison (handle various formats)
            backend_name_normalized = backend_name.lower().strip()

            # Find matching backend by name or class name
            for backend in backends:
                backend_class_name = backend.__class__.__name__
                backend_class_name_lower = backend_class_name.lower()
                backend_name_lower = backend.name.lower() if hasattr(backend, "name") else ""

                # Extract base name from class name (remove "AddressBackend")
                class_base_name = backend_class_name_lower.replace("addressbackend", "").strip()

                comparisons = [
                    backend_name_normalized == backend_name_lower,
                    backend_name_normalized == backend_class_name_lower,
                    backend_name == backend_class_name,
                    backend_name_normalized == class_base_name,
                    backend_name_normalized.endswith(backend_name_lower + "addressbackend"),
                    backend_name_normalized.endswith(backend_class_name_lower),
                    backend_name_normalized == (class_base_name + "addressbackend"),
                    backend_name_normalized.startswith(backend_name_lower)
                    and "addressbackend" in backend_name_normalized,
                    backend_name_normalized.startswith(class_base_name)
                    and "addressbackend" in backend_name_normalized,
                ]

                if any(comparisons):
                    return backend.label or backend.display_name or backend.name or backend_name

            # Fallback: try to format the backend name nicely
            # Remove "AddressBackend" or "addressbackend" suffix if present (case-insensitive)
            formatted = backend_name
            for suffix in ["AddressBackend", "addressbackend", "Addressbackend", "addressBackend"]:
                if formatted.lower().endswith(suffix.lower()):
                    formatted = formatted[: -len(suffix)]
                    break

            # Format nicely: replace underscores with spaces and title case
            formatted = formatted.replace("_", " ").strip()
            if formatted:
                # Handle camelCase or lowercase words
                if formatted.islower():
                    formatted = formatted.title()
                else:
                    # If it's already mixed case, try to split camelCase
                    import re

                    formatted = re.sub(r"(?<!^)(?=[A-Z])", " ", formatted).title()

                return formatted

            return backend_name
        except Exception:
            # Fallback: try simple formatting if error occurs
            formatted = backend_name
            for suffix in ["AddressBackend", "addressbackend"]:
                if formatted.lower().endswith(suffix.lower()):
                    formatted = formatted[: -len(suffix)].replace("_", " ").title()
                    return formatted
            return backend_name

    @admin.display(description=_("Confidence"))
    def confidence_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = obj.raw_payload
        normalized = payload.get("normalized_address") or {}
        confidence = payload.get("confidence") or normalized.get("confidence")
        if confidence is not None:
            try:
                conf_value = float(confidence)
                return f"{conf_value:.1%}"
            except (TypeError, ValueError):
                return str(confidence)
        return "—"

    @admin.display(description=_("Raw payload"))
    def raw_payload_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        if len(payload) > 512:
            payload = payload[:512] + "…"
        return format_html(
            '<pre style="white-space: pre-wrap; max-width: 520px;">{}</pre>',
            payload,
        )


__all__ = ["AddressBackendInfoAdmin", "AddressLookupAdmin"]
