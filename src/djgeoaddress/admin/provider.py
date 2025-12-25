"""Admin for provider model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models.provider import ProviderModel


class PackagesInstalledFilter(admin.SimpleListFilter):
    """Filter for packages installed status using pkg alias."""

    title = _("Packages installed")
    parameter_name = "pkg"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


class ServicesImplementedFilter(admin.SimpleListFilter):
    """Filter for services implemented status using svc alias."""

    title = _("Services implemented")
    parameter_name = "svc"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


class ConfigReadyFilter(admin.SimpleListFilter):
    """Filter for config ready status using cfg alias."""

    title = _("Config ready")
    parameter_name = "cfg"

    def lookups(self, request, model_admin):
        return (
            ("1", _("Yes")),
            ("0", _("No")),
        )

    def queryset(self, request, queryset):
        return queryset


@admin.register(ProviderModel)
class ProviderAdmin(admin.ModelAdmin):
    """Simple admin for geoaddress providers."""

    list_display = [
        "name",
        "display_name",
        "description",
        "are_packages_installed",
        "are_services_implemented",
        "is_config_ready",
        "documentation_url",
        "site_url",
    ]
    list_filter = [PackagesInstalledFilter, ServicesImplementedFilter, ConfigReadyFilter]
    search_fields = ["name", "display_name", "description"]
    readonly_fields = [
        "name",
        "display_name",
        "description",
        "required_packages",
        "documentation_url",
        "site_url",
        "config_keys",
        "config_required",
        "config_prefix",
        "services",
        "are_packages_installed",
        "are_services_implemented",
        "is_config_ready",
    ]
    fieldsets = [
        (None, {
            "fields": ["name", "display_name", "description", "status_url", "documentation_url", "site_url"],
        }),
        (_("Packages"), {
            "fields": ["required_packages", "are_packages_installed", "missing_packages"],
        }),
        (_("Config"), {
            "fields": ["config_keys", "config_required", "config_prefix", "is_config_ready", "missing_config_keys"],
        }),
        (_("Services"), {
            "fields": ["services", "are_services_implemented", "missing_services"],
        }),
    ]

    def get_queryset(self, request):
        """Get queryset with query_string and attribute_search parameters from request."""
        from ..managers.provider import ProviderManager
        
        query_string = request.GET.get("q", "").strip()
        attribute_search = {}
        
        for alias, attr_name in ProviderManager.param_aliases.items():
            alias_value = request.GET.get(alias, "").strip()
            if alias_value:
                attribute_search[attr_name] = alias_value
        
        manager = ProviderModel.objects
        if query_string or attribute_search:
            return manager.search(
                query_string=query_string,
                attribute_search=attribute_search if attribute_search else None,
            )
        return manager.get_queryset()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

