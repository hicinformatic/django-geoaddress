"""Admin for provider model."""

from django.contrib import admin

from djproviderkit.admin.provider import BaseProviderAdmin

from ..models.provider import GeoaddressProviderModel


@admin.register(GeoaddressProviderModel)
class ProviderAdmin(BaseProviderAdmin):
    """Admin for geoaddress providers."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
