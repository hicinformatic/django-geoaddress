from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset import InMemoryQuerySet  # type: ignore[import-not-found]


class AddressLookupQuerySet(InMemoryQuerySet):
    """In-memory queryset for address lookup suggestions."""

    pass


class AddressLookupManager(models.Manager):
    def get_queryset(self):
        return AddressLookupQuerySet(model=self.model, data=[])


class AddressLookup(models.Model):
    label = models.CharField(max_length=512, verbose_name=_("Suggested address"))
    backend_used = models.CharField(
        max_length=64, blank=True, verbose_name=_("Backend used")
    )
    backend_reference = models.CharField(
        max_length=128, blank=True, verbose_name=_("Backend reference")
    )
    raw_payload = models.JSONField(default=dict, blank=True)

    objects = AddressLookupManager()

    class Meta:
        managed = False
        verbose_name = _("Address suggestion")
        verbose_name_plural = _("Address suggestions")
        ordering = []
        default_permissions = ()

    def __str__(self):
        return self.label or _("Address suggestion")

    @property
    def relevance(self) -> float:
        """Get relevance score from raw_payload."""
        if not self.raw_payload:
            return 0.0
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        relevance = payload.get("relevance") or normalized.get("relevance")
        if relevance is not None:
            try:
                return float(relevance)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    @property
    def confidence(self) -> float:
        """Get confidence score from raw_payload."""
        if not self.raw_payload:
            return 0.0
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        confidence = payload.get("confidence") or normalized.get("confidence")
        if confidence is not None:
            try:
                return float(confidence)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    @property
    def address_line1(self) -> str:
        """Get address line 1 from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["address_line1", "line1", "street", "street_address", "housenumber"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def address_line2(self) -> str:
        """Get address line 2 from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["address_line2", "line2", "neighbourhood"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def address_line3(self) -> str:
        """Get address line 3 from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["address_line3", "line3", "borough"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def city(self) -> str:
        """Get city from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["city", "town", "locality", "localadmin", "municipality", "county", "village"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def postal_code(self) -> str:
        """Get postal code from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["postal_code", "postalcode", "postcode", "zip", "zipcode"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def state(self) -> str:
        """Get state from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["state", "region", "province", "administrative_area", "state_district"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def country(self) -> str:
        """Get country from raw_payload."""
        if not self.raw_payload:
            return ""
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        address_dict = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        for key in ["country", "country_code", "country_a"]:
            value = payload.get(key) or normalized.get(key) or address_dict.get(key)
            if value:
                return str(value)
        return ""

    @property
    def latitude(self) -> float:
        """Get latitude from raw_payload."""
        if not self.raw_payload:
            return 0.0
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        lat = payload.get("latitude") or normalized.get("latitude")
        if lat is not None:
            try:
                return float(lat)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    @property
    def longitude(self) -> float:
        """Get longitude from raw_payload."""
        if not self.raw_payload:
            return 0.0
        payload = self.raw_payload
        normalized = payload.get("normalized_address") or {}
        lon = payload.get("longitude") or normalized.get("longitude")
        if lon is not None:
            try:
                return float(lon)
            except (TypeError, ValueError):
                return 0.0
        return 0.0
