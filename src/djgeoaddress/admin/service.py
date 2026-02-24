from djproviderkit.admin.service import ProviderServiceAdmin
from djgeoaddress.models.service import GeoaddressServiceModel
from django.contrib import admin

@admin.register(GeoaddressServiceModel)
class GeoaddressServiceAdmin(ProviderServiceAdmin):
    """Admin for geoaddress services."""
    pass