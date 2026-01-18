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
from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS

address_list_display = list(GEOADDRESS_FIELDS_DESCRIPTIONS.keys())


class BackendNameFilter(admin.SimpleListFilter):
    title = _("Backend")
    parameter_name = "bck"

    def lookups(self, request, model_admin):
        providers = ProviderModel.objects.get_queryset()
        return [(provider.name, provider.display_name) for provider in providers]

    def queryset(self, request, queryset):
        return queryset


class FirstFilter(admin.SimpleListFilter):
    title = _("First")
    parameter_name = "first"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


@admin.register(AddressModel)
class AddressAdmin(AdminBoostModel):
    boost_views = [
        "address_autocomplete_view",
    ]
    list_display = address_list_display 
    list_filter = [BackendNameFilter, FirstFilter]
    search_fields = ["address_line1", "backend"]
    readonly_fields = [
        "address_line1",
        "backend",

    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "text",
                    "address_line1",
                    "address_line2",
                    "address_line3",
                    "city",
                    "postal_code",
                    "state",
                    "region",
                    "country",
                    "country_code",
                    "municipality",
                    "neighbourhood",
                    "address_type",
                    "latitude",
                    "longitude",
                    "osm_id",
                    "osm_type",
                    "confidence",
                    "relevance",
                    "backend",
                    "backend_name",
                    "geoaddress_id",
                ],
            },
        ),
    ]

    def get_queryset(self, request: HttpRequest) -> Any:
        query = request.GET.get("q")
        if query:
            kwargs = {
                "first": bool(request.GET.get("first")),
                "backend": request.GET.get("bck"),
                "query": query,
            }
            manager = AddressManager(**kwargs)
            manager.model = self.model
            return manager.get_queryset()
        return AddressModel.objects.none()

    def get_search_results(self, request: HttpRequest, queryset: Any, search_term: str) -> tuple[Any, bool]:
        if search_term:
            return queryset, False
        return queryset, False

    def backend_name_display(self, obj: AddressModel | None) -> str:
        if not obj or not obj.backend_name:
            return "-"

        try:
            provider = ProviderModel.objects.get_queryset().filter(name=obj.backend_name).first()
            if provider:
                url = reverse("admin:djgeoaddress_providermodel_change", args=[provider.name])
                return format_html('<a href="{}">{}</a>', url, obj.backend_name)
        except (ValueError, TypeError):
            pass

        return obj.backend_name

    backend_name_display.short_description = _("Backend name")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_object(
        self, request: HttpRequest, object_id: str, from_field: str | None = None
    ) -> AddressModel | None:
        query = request.GET.get("q")
        if query:
            kwargs = {
                "query": query,
            }
            manager = AddressManager(**kwargs)
            manager.model = self.model
            qs = manager.get_queryset()
            return next((obj for obj in qs if obj.geoaddress_id == object_id), None)
        return None

    @admin_boost_view("json", "Autocomplete View")
    def address_autocomplete_view(self, request: HttpRequest) -> dict[str, Any]:
        search_term = request.GET.get("term") or request.GET.get("q")
        if search_term:
            kwargs = {
                "query": search_term,
                "first": True,
            }
            manager = AddressManager(**kwargs)
            manager.model = self.model
            qs = manager.get_queryset()
        else:
            qs = AddressModel.objects.none()
        from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS

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
