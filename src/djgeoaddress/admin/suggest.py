"""Admin for address suggestion model."""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django_boosted import AdminBoostModel, admin_boost_view

from ..managers.suggest import AddressManager
from ..models.provider import ProviderModel
from ..models.suggest import AddressModel
from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS, GEOADDRESS_FIELDS_SEARCH




@admin.register(AddressModel)
class AddressAdmin(AdminBoostModel):
    boost_views = [
        "address_autocomplete_view",
    ]
    list_display = ["text_full", "backend_name_display"]
    search_fields = ["address_line1", "backend"]
    readonly_fields = [
        "address_line1",
        "backend",

    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def backend_name_display(self, obj: AddressModel | None) -> str:
        if not obj or not obj.backend or not obj.backend_name:
            return "-"
        url = reverse("admin:djgeoaddress_providermodel_change", args=[obj.backend])
        return format_html('<a href="{}">{}</a>', url, obj.backend_name)
    backend_name_display.short_description = _("Backend name")

    def get_object(self, request: HttpRequest, object_id: str, from_field: str | None = None) -> AddressModel | None:
        qs = self.model.objects.reverse_geocode(geoaddress_id=object_id)
        return qs.first()

    def get_queryset(self, request: HttpRequest) -> Any:
        query = request.GET.get("q")
        if query:
            kwargs = {
                "first": bool(request.GET.get("first")),
                "backend": request.GET.get("bck"),
            }
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
            "results": [
                {
                    "id": str(obj.pk),
                    "text": str(obj),
                    **{field: getattr(obj, field) for field in GEOADDRESS_FIELDS_DESCRIPTIONS}
                }
                for obj in qs
            ],
            "pagination": {
                "more": False,
            },
        }
