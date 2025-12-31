"""Models for tests.app."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from djgeoaddress.fields import GeoaddressField
from djgeoaddress.models.provider import ProviderModel


class Location(models.Model):
    """Model to test GeoaddressField."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Location name"),
    )
    provider = models.ForeignKey(
        ProviderModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Provider"),
        help_text=_("Geoaddress provider"),
    )
    address = GeoaddressField()
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        if self.address and self.address.get("text"):
            return f"{self.name} - {self.address['text']}"
        return self.name

