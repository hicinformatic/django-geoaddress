"""Models for tests.app."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from djgeoaddress.fields import GeoaddressField

class Addressbook(models.Model):
    """Address book model to test Location inline in admin."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Address book name"),
    )


class Location(models.Model):
    """Model to test GeoaddressField."""
    addressbook = models.ForeignKey(
        Addressbook,
        on_delete=models.SET_NULL,
        related_name="locations",
        verbose_name=_("Address book"),
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Location name"),
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

