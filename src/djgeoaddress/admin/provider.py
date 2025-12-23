"""Admin for provider model."""

from django.contrib import admin

from ..models.provider import ProviderModel


@admin.register(ProviderModel)
class ProviderAdmin(admin.ModelAdmin):
    """Simple admin for geoaddress providers."""

    list_display = [
        "name",
        "display_name",
        "description",
        "is_available",
        "is_configured",
        "documentation_url",
        "site_url",
    ]
    list_filter = ["is_available", "is_configured"]
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
        "is_available",
        "is_configured",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

