"""Admin for address backend diagnostics."""

from __future__ import annotations

from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http import JsonResponse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..models.address_backend import AddressBackendInfo, AddressBackendInfoQuerySet
from .utils import find_object_by_identifier, get_object_with_identifier, render_settings_row


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

        try:
            queryset_list = []
            for obj in queryset:
                queryset_list.append(obj)
        except (TypeError, AttributeError, StopIteration):
            return queryset, False

        if not queryset_list:
            return AddressBackendInfoQuerySet(model=self.model, data=[]), False

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

        filtered = [obj for obj in queryset_list if _matches(obj)]
        return AddressBackendInfoQuerySet(model=self.model, data=filtered), False

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "autocomplete/",
                self.admin_site.admin_view(self.backend_autocomplete_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_autocomplete",
            ),
        ]
        return custom_urls + urls

    def backend_autocomplete_view(self, request):
        from django.http import JsonResponse

        term = request.GET.get("term") or request.GET.get("q", "").strip()
        if not term:
            return JsonResponse({"results": []})

        queryset = self.get_queryset(request)
        filtered_queryset, use_distinct = self.get_search_results(request, queryset, term)

        results = []
        try:
            for obj in filtered_queryset:
                results.append(
                    {
                        "id": str(obj.pk),
                        "text": str(obj),
                    }
                )
        except (TypeError, AttributeError, StopIteration):
            pass

        return JsonResponse({"results": results})

    def get_object(self, request, object_id, from_field=None):
        return get_object_with_identifier(self, request, object_id, from_field)

    def _all_backend_configs(self):
        return get_backend_configs()

    def _get_backend_config_for_path(self, class_path: str | None):
        return get_backend_config_for_path(class_path)

    def _get_backend_info(self, backend_name: str):
        try:
            queryset = self.get_queryset(None)
            try:
                return queryset.get(pk=backend_name)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return find_object_by_identifier(queryset, backend_name)
        except Exception:
            return None

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

        non_sensitive_keys = {
            "NOMINATIM_BASE_URL",
            "NOMINATIM_USER_AGENT",
            "PHOTON_BASE_URL",
        }

        backend_config = self._get_backend_config_for_path(obj.class_path)
        config_dict = backend_config.get("config", {}) if backend_config else {}

        rows = []
        for key, present, preview in entries:
            actual_value = config_dict.get(key)

            is_configured = present and actual_value is not None and str(actual_value).strip() != ""

            if is_configured:
                icon = mark_safe('<span style="color: #198754; font-weight: bold;">✓</span>')
                status_text = mark_safe('<span style="color: #198754;">Configured</span>')

                if key in non_sensitive_keys:
                    value_html = format_html("<code>{}</code>", str(actual_value))
                else:
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
            diagnostic = getattr(backend, "_diagnostic", {})
            backend_name = diagnostic.get("backend_name") or backend.name
            choices.append((backend_name, display_name))
        return choices

    def queryset(self, request, queryset):
        return queryset


__all__ = ["AddressBackendInfoAdmin", "BackendFilter", "get_backend_configs", "get_backend_config_for_path"]

