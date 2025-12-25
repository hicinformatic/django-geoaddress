"""Provider model for geoaddress providers."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset.models import VirtualModel

from ..managers.provider import ProviderManager


class ProviderModel(VirtualModel):
    """Virtual model for geoaddress providers."""

    name = models.CharField(max_length=255, verbose_name=_("Name"), help_text=_("Provider name (e.g., nominatim)"), primary_key=True)
    display_name = models.CharField(max_length=255, verbose_name=_("Display name"), help_text=_("Provider display name"))
    description = models.TextField(blank=True, verbose_name=_("Description"), help_text=_("Provider description"))
    required_packages = models.JSONField(default=list, verbose_name=_("Required packages"), help_text=_("Required Python packages"))
    status_url = models.URLField(blank=True, verbose_name=_("Status URL"), help_text=_("Provider status URL"))
    documentation_url = models.URLField(blank=True, verbose_name=_("Documentation URL"), help_text=_("Provider documentation URL"))
    site_url = models.URLField(blank=True, verbose_name=_("Site URL"), help_text=_("Provider website URL"))
    config_keys = models.JSONField(default=list, verbose_name=_("Config keys"), help_text=_("Configuration keys"))
    config_required = models.JSONField(default=list, verbose_name=_("Config required"), help_text=_("Required configuration keys"))
    config_prefix = models.CharField(max_length=255, blank=True, verbose_name=_("Config prefix"), help_text=_("Configuration prefix"))
    services = models.JSONField(default=list, verbose_name=_("Services"), help_text=_("Available services"))
    are_packages_installed = models.BooleanField(default=False, verbose_name=_("Packages installed"), help_text=_("Whether required packages are installed"))
    are_services_implemented = models.BooleanField(default=False, verbose_name=_("Services implemented"), help_text=_("Whether services are implemented"))
    is_config_ready = models.BooleanField(default=False, verbose_name=_("Config ready"), help_text=_("Whether configuration is ready"))
    missing_packages = models.JSONField(default=list, verbose_name=_("Missing packages"), help_text=_("Missing packages"))
    missing_config_keys = models.JSONField(default=list, verbose_name=_("Missing config keys"), help_text=_("Missing config keys"))
    missing_services = models.JSONField(default=list, verbose_name=_("Missing services"), help_text=_("Missing services"))

    objects = ProviderManager()

    class Meta:
        managed = False
        verbose_name = _("Geoaddress Provider")
        verbose_name_plural = _("Geoaddress Providers")

    def __str__(self) -> str:
        return self.display_name or self.name
