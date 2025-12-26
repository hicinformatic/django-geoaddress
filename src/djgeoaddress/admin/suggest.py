"""Admin for address suggestion model."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

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
class AddressAdmin(admin.ModelAdmin):
    """Simple admin for address suggestions."""

    list_display = [
        "text",
        "city",
        "postal_code",
        "country",
        "latitude",
        "longitude",
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
        (None, {
            "fields": ["text", "reference", "address_line1", "address_line2", "address_line3", "city", "postal_code", "state", "region", "country", "country_code", "municipality", "neighbourhood", "address_type", "latitude", "longitude", "osm_id", "osm_type", "confidence", "relevance", "backend", "backend_name", "geoaddress_id", "search_used"],
        }),
    ]



    def get_queryset(self, request):
        """Get queryset."""
        kwargs = {
            "backend": request.GET.get("bck"),
            "first": bool(request.GET.get("first")),
            "query": request.GET.get("q"),
        }
        manager = AddressManager(**kwargs)
        manager.model = self.model
        return manager.get_queryset()

    def get_search_results(self, request, queryset, search_term):
        """Handle search for VirtualModel using AddressManager."""

        return queryset, False

    def backend_name_display(self, obj):
        """Display backend_name as a link to provider admin."""
        if not obj or not obj.backend_name:
            return "-"
        
        try:
            provider = ProviderModel.objects.get_queryset().filter(name=obj.backend_name).first()
            if provider:
                url = reverse("admin:djgeoaddress_providermodel_change", args=[provider.name])
                return format_html('<a href="{}">{}</a>', url, obj.backend_name)
        except Exception:
            pass
        
        return obj.backend_name
    
    backend_name_display.short_description = _("Backend name")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_object(self, request, object_id, from_field=None):
        """Get address object by geoaddress_id using get_address_by_reference."""
        print("get_object", object_id)
        parts = object_id.split("-", 1)
        if len(parts) != 2:
            return None
        backend_name, reference = parts
        kwargs = {
            "reference": reference,
            "backend": backend_name,
        }
        print("get_object", kwargs)
        manager = AddressManager(**kwargs)
        manager.model = self.model
        qs = manager.get_queryset()
        print("qs", qs)
        return qs.first()
