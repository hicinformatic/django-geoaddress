"""Provider model for geoaddress providers."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset.models import VirtualModel

from ..managers.provider import ProviderManager


class ProviderModel(VirtualModel):
    """Virtual model for geoaddress providers."""

    name = models.CharField(max_length=255, verbose_name=_("Name"), help_text=_("Provider name (e.g., nominatim)"))
    display_name = models.CharField(max_length=255, verbose_name=_("Display name"), help_text=_("Provider display name"))
    description = models.TextField(blank=True, verbose_name=_("Description"), help_text=_("Provider description"))
    required_packages = models.JSONField(default=list, verbose_name=_("Required packages"), help_text=_("Required Python packages"))
    documentation_url = models.URLField(blank=True, verbose_name=_("Documentation URL"), help_text=_("Provider documentation URL"))
    site_url = models.URLField(blank=True, verbose_name=_("Site URL"), help_text=_("Provider website URL"))
    config_keys = models.JSONField(default=list, verbose_name=_("Config keys"), help_text=_("Configuration keys"))
    config_required = models.JSONField(default=list, verbose_name=_("Config required"), help_text=_("Required configuration keys"))
    config_prefix = models.CharField(max_length=255, blank=True, verbose_name=_("Config prefix"), help_text=_("Configuration prefix"))
    services = models.JSONField(default=list, verbose_name=_("Services"), help_text=_("Available services"))
    is_available = models.BooleanField(default=False, verbose_name=_("Is available"), help_text=_("Whether provider is available"))
    is_configured = models.BooleanField(default=False, verbose_name=_("Is configured"), help_text=_("Whether provider is configured"))

    objects = ProviderManager()

    class Meta:
        managed = False
        verbose_name = _("Geoaddress Provider")
        verbose_name_plural = _("Geoaddress Providers")

    def __str__(self) -> str:
        return self.display_name or self.name

