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
    """Simple admin for address suggestions."""

    boost_views = [
        "address_autocomplete_view",
    ]
    list_display = [
        "text",
        "city",
        "postal_code",
        "country",
        "latitude",
        "longitude",
        "confidence",
        "relevance",
        "region",
        "backend_name_display",
    ]
    list_filter = [BackendNameFilter, FirstFilter]
    search_fields = ["text", "city", "postal_code", "country"]
    readonly_fields = [
        "text",
        "reference",
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
        "search_used",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "text",
                    "reference",
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
                    "search_used",
                ],
            },
        ),
    ]

    def get_queryset(self, request: HttpRequest, **kwargs: Any) -> Any:
        """Get queryset with optional query filter.

        Args:
            request: Django request object
            **kwargs: Additional keyword arguments

        Returns:
            QuerySet of AddressModel instances
        """
        query = kwargs.get("query", request.GET.get("q"))
        if query:
            kwargs = {
                "first": kwargs.get("first") or bool(request.GET.get("first")),
                "backend": kwargs.get("backend") or request.GET.get("bck"),
                "query": query,
            }
            manager = AddressManager(**kwargs)
            manager.model = self.model
            return manager.get_queryset()
        return AddressModel.objects.none()

    def backend_name_display(self, obj: AddressModel | None) -> str:
        """Display backend_name as a link to provider admin.

        Args:
            obj: AddressModel instance

        Returns:
            HTML link or backend name string
        """
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

    def get_object_by_reference(self, backend: str, reference: str) -> AddressModel | None:
        """Get address object by reference.

        Args:
            backend: Backend name
            reference: Address reference ID

        Returns:
            AddressModel instance or None
        """
        kwargs = {
            "reference": reference,
            "backend": backend,
        }
        manager = AddressManager(**kwargs)
        manager.model = self.model
        qs = manager.get_queryset()
        return qs.first()

    def get_object_by_search(
        self, request: HttpRequest, reference: str, backend: str
    ) -> AddressModel | None:
        """Get address object by search query.

        Args:
            request: Django request object
            reference: Address reference ID
            backend: Backend name

        Returns:
            AddressModel instance or None
        """
        query = request.GET.get("q")
        if not query:
            return None
        kwargs = {
            "query": query,
            "backend": backend,
        }
        manager = AddressManager(**kwargs)
        manager.model = self.model
        qs = manager.get_queryset()
        return next((obj for obj in qs if obj.reference == reference), None)

    def get_object(
        self, request: HttpRequest, object_id: str, from_field: str | None = None
    ) -> AddressModel | None:
        """Get address object by geoaddress_id.

        Args:
            request: Django request object
            object_id: Combined backend_name-reference ID
            from_field: Optional field name (unused)

        Returns:
            AddressModel instance or None
        """
        parts = object_id.split("-", 1)
        if len(parts) != 2:
            return None
        obj = self.get_object_by_reference(parts[0], parts[1])
        if obj is None:
            obj = self.get_object_by_search(request, parts[1], parts[0])
        return obj

    @admin_boost_view("json", "Autocomplete View")
    def address_autocomplete_view(self, request: HttpRequest) -> dict[str, Any]:
        """Autocomplete view for address suggestions.

        Args:
            request: Django request object with 'term' query parameter

        Returns:
            Dictionary with results and pagination info
        """
        search_term = request.GET.get("term") or request.GET.get("q")
        qs = self.get_queryset(request, query=search_term, first=True)
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
