"""Admin for address suggestion model."""

from django.contrib import admin

from ..managers.suggest import AddressManager
from ..models.suggest import AddressModel


@admin.register(AddressModel)
class AddressAdmin(admin.ModelAdmin):
    """Simple admin for address suggestions."""

    list_display = [
        "text",
        "city",
        "postal_code",
        "country",
        "latitude",
        "longitude",
        "backend_name",
    ]
    list_filter = ["backend_name", "country_code"]
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
    ]

    def get_queryset(self, request):
        """Get queryset with query parameter from request."""
        query = request.GET.get("q", "")
        if query:
            manager = AddressManager(query=query)
            manager.model = self.model
            return manager.get_queryset()
        return super().get_queryset(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

