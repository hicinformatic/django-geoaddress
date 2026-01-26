"""Admin for address suggestion model."""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
import json

from django_boosted import AdminBoostModel, admin_boost_view

from ..models.suggest import AddressModel
from ..models.provider import GeoaddressProviderModel
from geoaddress import (
    GEOADDRESS_FIELDS_DESCRIPTIONS,
    GEOADDRESS_FIELDS_ESSENTIALS,
    GEOADDRESS_FIELDS_OPTIONALS,
    GEOADDRESS_FIELDS_COORDINATES,
)

from djproviderkit.admin.service import FirstServiceAdminFilter, BackendServiceAdminFilter

BackendServiceAdminFilter.provider_model = GeoaddressProviderModel

@admin.register(AddressModel)
class AddressAdmin(AdminBoostModel):
    boost_views = [
        "address_autocomplete_view",
    ]
    list_filter = [FirstServiceAdminFilter, BackendServiceAdminFilter]
    list_display = ["text_full", "backend_name_display"]
    search_fields = ["address_line1", "backend"]
    readonly_fields = [
        "address_line1",
        "backend",

    ]

    def change_fieldsets(self):
        self.add_to_fieldset(None, GEOADDRESS_FIELDS_ESSENTIALS.keys())
        self.add_to_fieldset(_("Optionals"), GEOADDRESS_FIELDS_OPTIONALS.keys())
        self.add_to_fieldset(_("Coordinates"), GEOADDRESS_FIELDS_COORDINATES.keys())
        self.add_to_fieldset(_("Backend"), ["backend_name_display", "geoaddress_id", "raw_result"])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def backend_name_display(self, obj: AddressModel | None) -> str:
        if not obj or not obj.backend or not obj.backend_name:
            return "-"
        url = reverse("admin:djgeoaddress_geoaddressprovidermodel_change", args=[obj.backend])
        return format_html('<a href="{}">{}</a>', url, obj.backend_name)
    backend_name_display.short_description = _("Backend name")

    def raw_result(self, obj: AddressModel | None) -> str:
        raw = self.model.objects.get_raw_result(command="reverse_geocode")
        raw = json.dumps(raw[0].get("result"), indent=4, ensure_ascii=False)
        return mark_safe(f"<pre>{raw}</pre>")
    raw_result.short_description = _("Raw result")

    def get_object(self, request: HttpRequest, object_id: str, _from_field: str | None = None) -> AddressModel | None:
        qs = self.model.objects.reverse_geocode(geoaddress_id=object_id)
        return qs.first()

    def get_queryset(self, request: HttpRequest) -> Any:
        query = request.GET.get("q")
        if query:
            kwargs = {"first": bool(request.GET.get("first"))}
            if request.GET.get("bck"):
                kwargs["attribute_search"] = {"name": request.GET.get("bck")}
            return self.model.objects.search_addresses(query=query, **kwargs)
        return self.model.objects.none()

    def get_search_results(self, request: HttpRequest, queryset: Any, search_term: str) -> tuple[Any, bool]:
        if search_term:
            return queryset, False
        return queryset, False

    @admin_boost_view("json", "Autocomplete View")
    def address_autocomplete_view(self, request: HttpRequest) -> dict[str, Any]:
        search_term = request.GET.get("term") or request.GET.get("q")
        qs = self.model.objects.none()
        if search_term:
            kwargs = {
                "first": True,
            }
            qs = self.model.objects.addresses_autocomplete(query=search_term, **kwargs)
        return {
            "addresses": [
                {field: getattr(obj, field) for field in GEOADDRESS_FIELDS_DESCRIPTIONS}
                for obj in qs
            ],
            "pagination": {
                "more": False,
            },
        }
