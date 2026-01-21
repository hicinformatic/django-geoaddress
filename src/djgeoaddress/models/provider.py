"""Provider model for geoaddress providers."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset.models import VirtualModel
from geoaddress.providers.base import GeoaddressProvider
from djproviderkit.models.service import define_provider_fields, define_service_fields

from ..managers.provider import ProviderManager

services = list(GeoaddressProvider.services_cfg.keys())


@define_provider_fields(primary_key='name')
@define_service_fields(services)
class GeoaddressProviderModel(VirtualModel):
    """Virtual model for geoaddress providers."""

    name: models.CharField = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Provider name (e.g., nominatim)"),
        primary_key=True,
    )

    objects = ProviderManager()

    class Meta:
        managed = False
        app_label = 'djgeoaddress'
        verbose_name = _("Geoaddress Provider")
        verbose_name_plural = _("Geoaddress Providers")
        ordering = ['-priority', 'name']

    def __str__(self) -> str:
        return self.display_name or self.name
