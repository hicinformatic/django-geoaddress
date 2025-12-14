"""Admin for address suggestions and lookup."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, cast
from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib import admin, messages
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import JsonResponse, QueryDict
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..models.address_lookup import AddressLookup, AddressLookupQuerySet
from .address_backend import BackendFilter, get_backend_configs
from .utils import find_object_by_identifier, get_object_with_identifier

try:
    from geoaddress.helpers import (
        GEOADDRESS_FIELDS_NORMALIZED,
        get_address_backends_from_config as get_address_backends_fn,
        get_address_by_reference as get_address_by_reference_fn,
        search_addresses as search_addresses_fn,
    )
except ImportError:
    GEOADDRESS_FIELDS_NORMALIZED = {}
    search_addresses_fn = None
    get_address_backends_fn = None
    get_address_by_reference_fn = None


def _parse_address_term(term: str) -> Dict[str, Optional[str]]:
    """Extract postal_code (5 digits) and city from address string."""
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
    config_list: list[Dict[str, Any]],
    term: str,
    backend: Optional[str] = None,
    limit: Optional[int] = None,
    min_confidence: Optional[float] = None,
) -> list[Dict[str, Any]]:
    if not config_list or not term or search_addresses_fn is None:
        return []

    try:
        search_result = search_addresses_fn(
            backends_config=config_list,
            query=term,
            min_confidence=min_confidence if min_confidence is not None else 0.0,
            limit=limit if limit is not None else 20,
            backend=backend,
        )
    except Exception as exc:  # pragma: no cover - defensive
        error_detail = str(exc)
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
        if backend:
            error_msg = f"[Backend: {backend}] {error_msg}"
        return [{"label": f"Error: {error_msg}", "raw": {**search_result, "backend": backend}}]

    backend_name = search_result.get("backend_used") or ""
    results = search_result.get("results", [])

    if not results:
        return [{"label": "No result from backends", "raw": {"error": "No result"}}]

    rows = []
    for result in results:
        raw = {k: v for k, v in (result or {}).items() if k != "_raw_response"}
        if backend_name and not raw.get("backend_used"):
            raw["backend_used"] = backend_name
        normalized = raw.get("normalized_address") or {}
        backend_reference = (
            raw.get("backend_reference")
            or raw.get("address_reference")
            or raw.get("reference")
            or normalized.get("backend_reference")
            or normalized.get("address_reference")
            or normalized.get("reference")
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
    """Remove warning messages from address labels."""
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


def _standardize_address_result_django(
    result: Dict[str, Any],
    *,
    backend_display: Optional[str] = None,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Standardize address result to consistent format for Django.

    Returns a dictionary with always the same fields:
    - text: formatted address string
    - reference: backend reference ID
    - address_line1, address_line2, address_line3
    - city, postal_code, state, region, country
    - municipality, neighbourhood, address_type
    - latitude, longitude
    - confidence, relevance
    - backend: backend display name
    - backend_name: simple backend name (from python-geoaddress)
    - geoaddress_id: combined backend_name-reference ID (from python-geoaddress)
    """
    text = (
        result.get("formatted_address") or result.get("text") or result.get("label") or query or ""
    )

    reference = (
        result.get("backend_reference")
        or result.get("address_reference")
        or result.get("reference")
        or None
    )

    def safe_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    standardized = {
        "text": text,
        "reference": reference,
        "address_line1": result.get("address_line1") or None,
        "address_line2": result.get("address_line2") or None,
        "address_line3": result.get("address_line3") or None,
        "city": result.get("city") or None,
        "postal_code": result.get("postal_code") or None,
        "state": result.get("state") or None,
        "region": result.get("region") or None,
        "country": result.get("country") or None,
        "municipality": result.get("municipality") or None,
        "neighbourhood": result.get("neighbourhood") or None,
        "address_type": result.get("address_type") or None,
        "latitude": safe_float(result.get("latitude")),
        "longitude": safe_float(result.get("longitude")),
        "confidence": safe_float(result.get("confidence")),
        "relevance": safe_float(result.get("relevance")),
        "backend": backend_display or result.get("backend") or result.get("backend_used") or None,
        "backend_name": result.get("backend_name"),
        "geoaddress_id": result.get("geoaddress_id"),
    }

    return standardized


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
        "relevance_display",
        "backend_display",
    ]
    search_fields = ["label", "backend_used", "backend_reference"]
    ordering = []
    list_per_page = 20
    list_display_links = ("reference_link",)
    change_list_template = "admin/change_list.html"
    list_filter = [BackendFilter]
    readonly_fields = [
        "reference_slug_display",
        "label",
        "backend_used",
        "backend_display",
        "backend_reference",
        "confidence_display",
        "relevance_display",
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
        "raw_response_display",
    ]
    fieldsets = (
        (
            _("Summary"),
            {
                "fields": (
                    "reference_slug_display",
                    "label",
                    "backend_display",
                    "backend_reference",
                    "confidence_display",
                    "relevance_display",
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
            _("Structured payload"),
            {
                "fields": ("raw_payload_full_display",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Raw API response"),
            {
                "fields": ("raw_response_display",),
                "classes": ("collapse",),
                "description": _(
                    "Original raw response from the backend API before normalization."
                ),
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
    _CACHE_TIMEOUT = 900

    def get_queryset(self, request):
        query = (request.GET.get("q") or "").strip()
        backend_name = (request.GET.get("backend") or "").strip()

        limit_param = request.GET.get("limit")
        limit = int(limit_param) if limit_param else None
        min_confidence_param = request.GET.get("min_confidence")
        min_confidence = float(min_confidence_param) if min_confidence_param else None

        configs = get_backend_configs()

        data = []
        if configs and query:
            for entry in build_address_suggestions(
                configs,
                query,
                backend=backend_name if backend_name else None,
                limit=limit,
                min_confidence=min_confidence,
            ):
                raw = entry.get("raw") or {}
                normalized = raw.get("normalized_address") or {}
                backend_reference = (
                    raw.get("backend_reference")
                    or raw.get("address_reference")
                    or raw.get("reference")
                    or normalized.get("backend_reference")
                    or normalized.get("address_reference")
                    or normalized.get("reference")
                    or ""
                )
                obj = AddressLookup(
                    label=entry.get("label") or "",
                    backend_used=raw.get("backend_used") or raw.get("backend") or "",
                    backend_reference=backend_reference,
                    raw_payload=raw,
                )
                slug_value = self._build_reference_slug(obj.backend_used, obj.backend_reference)
                if slug_value:
                    obj._lookup_slug = slug_value
                    obj.pk = slug_value
                    self._cache_payload(slug_value, raw, obj.backend_used)
                data.append(obj)

        queryset = AddressLookupQuerySet(model=AddressLookup, data=data)

        ordering_param = request.GET.get("o", "")
        if not ordering_param:
            queryset = queryset.order_by("-relevance", "-confidence")

        return queryset

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
        return queryset, False

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "autocomplete/",
                self.admin_site.admin_view(self.address_autocomplete_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_autocomplete",
            ),
        ]
        return custom_urls + urls

    def address_autocomplete_view(self, request):
        if request.GET.get("fetch_data"):
            term = request.GET.get("term", "").strip()
            if term:
                return self._handle_fetch_data_request(request, term)
            return JsonResponse({"data": None})

        term = request.GET.get("term") or request.GET.get("q", "").strip()
        if not term:
            return JsonResponse({"results": []})

        backend_name = request.GET.get("backend", "").strip()

        limit_param = request.GET.get("limit")
        min_confidence_param = request.GET.get("min_confidence")

        modified_get = QueryDict(mutable=True)
        modified_get.update(request.GET)
        modified_get["q"] = term
        if backend_name:
            modified_get["backend"] = backend_name
        if limit_param:
            modified_get["limit"] = limit_param
        if min_confidence_param:
            modified_get["min_confidence"] = min_confidence_param

        class ModifiedRequest:
            def __init__(self, original_request, modified_get):
                self.GET = modified_get
                self.user = original_request.user
                self.method = original_request.method

        modified_request = ModifiedRequest(request, modified_get)
        queryset = self.get_queryset(modified_request)

        results = []
        try:
            for obj in queryset:
                standardized = self._build_result_from_obj(obj, term)
                results.append(standardized)
        except (TypeError, AttributeError, StopIteration):
            pass

        return JsonResponse({"results": results})

    def _handle_fetch_data_request(self, request, term: str) -> JsonResponse:
        """Handle fetch_data request - return cached data for a term."""
        cache_key = f"geoaddress:addresslookup:{term}"
        cached_data = cache.get(cache_key)
        if not cached_data or not isinstance(cached_data, dict):
            return JsonResponse({"data": None})

        payload = cached_data.get("payload", {})
        normalized = payload.get("normalized_address") or payload
        result_data = normalized.copy() if isinstance(normalized, dict) else {}

        address_fields = [
            "address_line1",
            "address_line2",
            "address_line3",
            "city",
            "postal_code",
            "state",
            "region",
            "country",
            "municipality",
            "neighbourhood",
            "address_type",
            "latitude",
            "longitude",
            "confidence",
            "relevance",
            "formatted_address",
            "backend_reference",
            "address_reference",
            "backend_used",
            "backend",
            "backend_name",
            "geoaddress_id",
        ]
        for key in address_fields:
            if key in payload and key not in result_data:
                result_data[key] = payload[key]

        backend_used = result_data.get("backend_used") or payload.get("backend_used")
        backend_display = self._get_backend_display_name(backend_used)

        data = _standardize_address_result_django(
            result_data,
            backend_display=backend_display,
            query=term,
        )

        geoaddress_id = result_data.get("geoaddress_id")
        if geoaddress_id:
            data["id"] = geoaddress_id

        backend_reference = data.get("reference")
        admin_url = None
        if backend_used and backend_reference:
            slug_value = self._build_reference_slug(backend_used, backend_reference)
            if slug_value:
                try:
                    admin_url = reverse(
                        "admin:djgeoaddress_addresslookup_change", args=[slug_value]
                    )
                except Exception:
                    pass
        data["admin_url"] = admin_url

        return JsonResponse({"data": data})

    def _get_backend_display_name(self, backend_used: Optional[str]) -> Optional[str]:
        """Get backend display name from backend_used identifier."""
        if not backend_used:
            return None

        try:
            if get_address_backends_fn:
                backends = get_address_backends_fn(get_backend_configs())
                if backends:
                    for backend in backends:
                        if getattr(backend, "name", "").lower() == str(backend_used).lower():
                            return (
                                getattr(backend, "display_name", None)
                                or getattr(backend, "label", None)
                            )
        except Exception:
            pass
        return None

    def _extract_result_data_from_obj(self, obj: AddressLookup) -> Dict[str, Any]:
        """Extract address data from AddressLookup object."""
        result_data = {}

        if obj.raw_payload:
            payload = obj.raw_payload
            normalized = payload.get("normalized_address") or {}
            result_data = dict(normalized) if normalized else dict(payload)

            address_fields = [
                "address_line1",
                "address_line2",
                "address_line3",
                "city",
                "postal_code",
                "state",
                "region",
                "country",
                "municipality",
                "neighbourhood",
                "address_type",
                "latitude",
                "longitude",
                "confidence",
                "relevance",
                "formatted_address",
                "backend_reference",
                "address_reference",
                "backend_used",
                "backend",
                "backend_name",
                "geoaddress_id",
            ]
            for key in address_fields:
                if key in payload and key not in result_data:
                    result_data[key] = payload[key]

        if not result_data:
            result_data = {
                "address_line1": self._get_from_payload(obj, "address_line1"),
                "address_line2": self._get_from_payload(obj, "address_line2"),
                "address_line3": self._get_from_payload(obj, "address_line3"),
                "city": self._get_from_payload(obj, "city"),
                "postal_code": self._get_from_payload(obj, "postal_code"),
                "state": self._get_from_payload(obj, "state"),
                "region": self._get_from_payload(obj, "region"),
                "country": self._get_from_payload(obj, "country"),
                "municipality": self._get_from_payload(obj, "municipality"),
                "neighbourhood": self._get_from_payload(obj, "neighbourhood"),
                "address_type": self._get_from_payload(obj, "address_type"),
                "backend_reference": obj.backend_reference,
                "backend_used": obj.backend_used,
                "formatted_address": obj.label or str(obj),
            }
            if obj.raw_payload:
                payload = obj.raw_payload
                normalized = payload.get("normalized_address") or {}
                result_data["latitude"] = payload.get("latitude") or normalized.get("latitude")
                result_data["longitude"] = payload.get("longitude") or normalized.get("longitude")
                result_data["confidence"] = payload.get("confidence") or normalized.get(
                    "confidence"
                )
                result_data["relevance"] = payload.get("relevance") or normalized.get("relevance")

        return result_data

    def _build_result_from_obj(self, obj: AddressLookup, term: str) -> Dict[str, Any]:
        """Build standardized result dictionary from AddressLookup object."""
        result_data = self._extract_result_data_from_obj(obj)

        backend_display = self.backend_display(obj)
        backend_display_str = (
            backend_display if backend_display != "—" else (obj.backend_used or None)
        )

        standardized = _standardize_address_result_django(
            result_data,
            backend_display=backend_display_str,
            query=term,
        )

        reference = standardized.get("reference") or obj.backend_reference
        backend_used = obj.backend_used or ""
        
        addr_id = standardized.get("geoaddress_id") or result_data.get("geoaddress_id")
        if not addr_id and backend_used and reference:
            addr_id = f"{backend_used}-{reference}"
        elif not addr_id and reference:
            addr_id = reference
        elif not addr_id:
            addr_id = standardized.get("text", "") or ""

        standardized["id"] = addr_id

        slug_value = self._get_obj_slug(obj)
        admin_url = None

        if slug_value:
            try:
                admin_url = reverse(
                    "admin:djgeoaddress_addresslookup_change", args=[slug_value]
                )
            except Exception:
                pass

        if not admin_url and reference and backend_used:
            try:
                from ..fields import AddressField

                address_data = {
                    "backend_used": backend_used,
                    "backend_reference": reference,
                    "backend": backend_used,
                    "address_reference": reference,
                }
                admin_url = AddressField.get_admin_url(address_data)
            except Exception:
                pass

        standardized["admin_url"] = admin_url
        return standardized

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

    def _cache_payload(
        self, slug_value: Optional[str], payload: Dict[str, Any], backend_label: str
    ):
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
                normalized = payload.get("normalized_address", {})
                if isinstance(normalized, dict):
                    normalized_dict = normalized
                else:
                    normalized_dict = {}

                has_address_data = (
                    payload.get("address_line1")
                    or payload.get("line1")
                    or payload.get("city")
                    or normalized_dict.get("line1")
                    or normalized_dict.get("address_line1")
                    or normalized_dict.get("city")
                    or payload.get("formatted_address")
                    or payload.get("formatted")
                )
                if has_address_data and not payload.get("error"):
                    backend_label = cached_entry.get("backend_label") or backend_identifier
                    payload.setdefault("backend_reference", backend_reference)
                    payload.setdefault("backend_used", backend_identifier)
                    return payload, backend_label

        if get_address_by_reference_fn is None:
            return (
                {
                    "error": "python-geoaddress helpers are not available.",
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

        if payload and not payload.get("error"):
            payload.setdefault("backend_used", backend_identifier)
            payload.setdefault("backend_reference", backend_reference)
            payload.setdefault("address_reference", backend_reference)

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

    @admin.display(description=_("Reference"), ordering="backend_reference")
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
            label=self._derive_label_from_payload(payload) or backend_reference or backend_label,
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

        backend_identifier = self._normalize_backend_identifier(backend_name)
        if not backend_identifier:
            messages.error(request, _("Invalid backend identifier."))
            return None

        if get_address_by_reference_fn is None:
            messages.error(request, _("python-geoaddress helpers are not available."))
            return None

        payload = self._fetch_payload_from_backend(backend_identifier, backend_reference)
        if not payload:
            messages.error(request, _("Failed to fetch address data from backend."))
            return None

        backend_label = payload.get("backend_used") or backend_identifier

        cache_slug = object_id or self._build_reference_slug(backend_identifier, backend_reference)
        if cache_slug:
            self._cache_payload(cache_slug, payload, backend_label)

        if "error" in payload:
            error_msg = payload.get("error", "Unknown error")
            messages.warning(
                request,
                _("Backend response contains an error: %(error)s") % {"error": error_msg},
            )
            if not self._has_address_data(payload):
                return None

        return self._make_lookup_object(
            payload=payload,
            backend_label=backend_label or backend_name or "",
            backend_reference=backend_reference,
            slug_value=object_id,
        )

    @admin.display(description=_("Structured payload (JSON)"))
    def raw_payload_full_display(self, obj: AddressLookup):
        """Display the complete structured payload from the backend as formatted JSON."""
        if not obj.raw_payload:
            return mark_safe('<p style="color: #999;">—</p>')
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="white-space: pre-wrap; word-wrap: break-word; max-width: 100%; '
            'background-color: #f5f5f5; color: #212529; padding: 15px; border: 1px solid #ddd; '
            'border-radius: 4px; overflow-x: auto; font-family: monospace; font-size: 12px;">{}</pre>',
            payload,
        )

    @admin.display(description=_("Raw API response (JSON)"))
    def raw_response_display(self, obj: AddressLookup):
        """Display the original raw API response from the backend."""
        if not obj.raw_payload:
            return mark_safe('<p style="color: #999;">—</p>')
        raw_response = obj.raw_payload.get("_raw_response")
        if raw_response is None:
            return mark_safe(
                '<p style="color: #999; font-style: italic;">'
                "Raw response not available (only structured payload is stored)"
                "</p>"
            )
        raw_json = json.dumps(raw_response, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="white-space: pre-wrap; word-wrap: break-word; max-width: 100%; '
            'background-color: #fff3cd; color: #212529; padding: 15px; border: 1px solid #ffc107; '
            'border-radius: 4px; overflow-x: auto; font-family: monospace; font-size: 12px;">{}</pre>',
            raw_json,
        )

    def _fetch_payload_from_backend(
        self, backend_identifier: str, backend_reference: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch address payload from backend by reference.

        Returns:
            Payload dict if successful, None otherwise.
        """
        if get_address_by_reference_fn is None:
            return None

        configs = get_backend_configs()
        if not configs:
            return None

        backend_to_try = [backend_identifier, backend_identifier.lower()]
        payload = None
        raw_response = None

        if get_address_backends_fn:
            try:
                backends = get_address_backends_fn(configs)
                for backend_instance in backends:
                    backend_name = (
                        getattr(backend_instance, "name", "")
                        or backend_instance.__class__.__name__
                    )
                    backend_name_normalized = backend_name.lower().strip()
                    backend_identifier_normalized = backend_identifier.lower().strip()

                    if (
                        backend_name_normalized == backend_identifier_normalized
                        or backend_name.lower() == backend_identifier_normalized
                        or backend_identifier_normalized in backend_name_normalized
                        or backend_name_normalized in backend_identifier_normalized
                    ):
                        try:
                            raw_payload = backend_instance.get_address_by_reference(
                                backend_reference
                            )
                            if raw_payload and isinstance(raw_payload, dict):
                                raw_response = raw_payload.get("_raw_response")
                                break
                        except Exception:
                            continue
            except Exception:
                pass

        for backend_name_attempt in backend_to_try:
            try:
                payload = get_address_by_reference_fn(
                    configs,
                    backend=backend_name_attempt,
                    address_reference=backend_reference,
                )
                if payload and not payload.get("error"):
                    if raw_response is not None:
                        payload["_raw_response"] = raw_response
                    return cast(Dict[str, Any], payload)
                if payload and payload.get("error"):
                    error_msg = payload.get("error", "")
                    if "not found" not in error_msg.lower():
                        if raw_response is not None:
                            payload["_raw_response"] = raw_response
                        return cast(Dict[str, Any], payload)
            except Exception:
                continue

        return cast(Optional[Dict[str, Any]], payload)

    def _has_address_data(self, payload: Dict[str, Any]) -> bool:
        """Check if payload contains actual address data (not just empty structure)."""
        if not payload or not isinstance(payload, dict):
            return False

        address_fields = [
            "line1",
            "address_line1",
            "city",
            "postal_code",
            "formatted_address",
            "country",
        ]
        for key in address_fields:
            value = payload.get(key)
            if value is not None and str(value).strip():
                return True

        normalized = payload.get("normalized_address", {})
        if isinstance(normalized, dict):
            for key in address_fields:
                value = normalized.get(key)
                if value is not None and str(value).strip():
                    return True

        if payload.keys():
            structure_keys = [
                "address_line1",
                "city",
                "postal_code",
                "formatted_address",
                "normalized_address",
            ]
            if any(k in payload for k in structure_keys):
                return True

        return False

    def _get_from_payload(self, obj: AddressLookup, key: str) -> Optional[str]:
        """Extract value from normalized payload."""
        if not obj.raw_payload:
            return None
        payload = obj.raw_payload
        normalized = payload.get("normalized_address", {})
        if not isinstance(normalized, dict):
            normalized = {}
        value = normalized.get(key) or payload.get(key)
        return str(value) if value is not None else None


    @admin.display(description=_("Raw payload"))
    def raw_payload_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        if len(payload) > 512:
            payload = payload[:512] + "…"
        return format_html(
            '<pre style="white-space: pre-wrap; max-width: 520px; color: #212529;">{}</pre>',
            payload,
        )


# Generate display methods dynamically from GEOADDRESS_FIELDS_NORMALIZED
if GEOADDRESS_FIELDS_NORMALIZED:
    for field_name, description in GEOADDRESS_FIELDS_NORMALIZED.items():
        def _make_display_method(field: str = field_name, desc: str = description):
            @admin.display(description=_(desc), ordering=field)
            def display_method(self, obj: AddressLookup):
                if not obj.raw_payload:
                    return "—"
                value = obj.raw_payload.get(field)
                if value is None:
                    return "—"
                if field in ("latitude", "longitude") and isinstance(value, (int, float)):
                    return f"{float(value):.6f}"
                if field in ("confidence", "relevance") and isinstance(value, (int, float)):
                    return f"{float(value):.1f}%"
                return str(value)
            
            display_method.__name__ = f"{field}_display"
            return display_method
        
        method = _make_display_method()
        setattr(AddressLookupAdmin, f"{field_name}_display", method)


__all__ = [
    "AddressLookupAdmin",
    "build_address_suggestions",
    "_parse_address_term",
    "_clean_address_label",
    "_standardize_address_result_django",
]

