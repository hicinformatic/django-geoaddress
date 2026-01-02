"""Address suggestion model for geoaddress."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset.models import VirtualModel

from ..managers.suggest import AddressManager


class AddressModel(VirtualModel):
    """Virtual model for address suggestions from geoaddress."""

    text = models.CharField(
        max_length=500,
        verbose_name=_("Full formatted address string"),
        help_text=_("Full formatted address string"),
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Backend reference ID"),
        help_text=_("Backend reference ID (place ID)"),
    )
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address line 1"),
        help_text=_("Street number and name"),
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address line 2"),
        help_text=_("Building, apartment, floor"),
    )
    address_line3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address line 3"),
        help_text=_("Additional address info"),
    )
    city = models.CharField(
        max_length=255, blank=True, verbose_name=_("City"), help_text=_("City name")
    )
    postal_code = models.CharField(
        max_length=50, blank=True, verbose_name=_("Postal code"), help_text=_("Postal/ZIP code")
    )
    county = models.CharField(
        max_length=255, blank=True, verbose_name=_("County"), help_text=_("County name")
    )
    state = models.CharField(
        max_length=255, blank=True, verbose_name=_("State"), help_text=_("State/region/province")
    )
    region = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Region"),
        help_text=_("Region or administrative area"),
    )
    country = models.CharField(
        max_length=255, blank=True, verbose_name=_("Country"), help_text=_("Country name")
    )
    country_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Country code"),
        help_text=_("ISO country code (e.g., FR, US, GB)"),
    )
    municipality = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Municipality"),
        help_text=_("Municipality or local administrative unit"),
    )
    neighbourhood = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Neighbourhood"),
        help_text=_("Neighbourhood, quarter, or district"),
    )
    address_type = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address type"),
        help_text=_("Address type or place type"),
    )
    latitude = models.FloatField(
        null=True, blank=True, verbose_name=_("Latitude"), help_text=_("Latitude coordinate")
    )
    longitude = models.FloatField(
        null=True, blank=True, verbose_name=_("Longitude"), help_text=_("Longitude coordinate")
    )
    osm_id = models.CharField(
        max_length=255, blank=True, verbose_name=_("OSM ID"), help_text=_("OpenStreetMap ID")
    )
    osm_type = models.CharField(
        max_length=50, blank=True, verbose_name=_("OSM type"), help_text=_("OpenStreetMap type")
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Confidence"),
        help_text=_("Confidence score (0-100%)"),
    )
    relevance = models.FloatField(
        null=True, blank=True, verbose_name=_("Relevance"), help_text=_("Relevance score (0-100%)")
    )
    backend = models.CharField(
        max_length=255, blank=True, verbose_name=_("Backend"), help_text=_("Backend display name")
    )
    backend_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Backend name"),
        help_text=_("Simple backend name (e.g., nominatim)"),
    )
    geoaddress_id = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Geoaddress ID"),
        help_text=_("Combined backend_name-reference ID"),
        primary_key=True,
    )
    search_used = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Search used"),
        help_text=_("Search used to get this address"),
    )

    objects = AddressManager()

    class Meta:
        managed = False
        verbose_name = _("Address Suggestion")
        verbose_name_plural = _("Address Suggestions")

    def __str__(self) -> str:
        return self.text or f"Address {self.reference or 'unknown'}"
