from __future__ import annotations

import json
from typing import Any

from django.db import models
from django.forms.widgets import TextInput
from django.template.loader import render_to_string
from django.urls import reverse
from geoaddress import (
    GEOADDRESS_FIELDS_ESSENTIALS,
    GEOADDRESS_FIELDS_OPTIONALS,
    GEOADDRESS_FIELDS_COORDINATES,
    GEOADDRESS_FULL_FIELDS,
)


class GeoaddressValue(dict):
    """Simple wrapper to format address as string."""

    def __init__(self, data: dict[str, Any] | None = None):
        """Initialize with address data."""
        super().__init__(data or {})

    def __str__(self) -> str:
        """Format address using GEOADDRESS_FIELDS_ESSENTIALS order."""
        parts = [str(self.get(k)) for k in GEOADDRESS_FIELDS_ESSENTIALS.keys() if self.get(k)]
        return ", ".join(parts)


class GeoaddressAutocompleteWidget(TextInput):
    """Widget to store geoaddress data via AddressModel with autocomplete."""

    template_name = "djgeoaddress/autocomplete.html"
    address_url_name = "djgeoaddress:redirect_to_address_list"
    redirect_url = "djgeoaddress:redirect_to_address"

    def get_url(self) -> str:
        """Return the autocomplete URL.

        Returns:
            Autocomplete URL string
        """
        return reverse(self.address_url_name)

    def render(
        self, name: str, value: Any, attrs: dict[str, Any] | None = None, renderer: Any = None
    ) -> str:
        autocomplete_url = self.get_url()
        try:
            values = json.loads(value) if value else {}
            
        except (json.JSONDecodeError, TypeError):
            values = {}

        geoaddress_data = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": v.get("label", k),
            }
            for k, v in GEOADDRESS_FIELDS_ESSENTIALS.items()
        }
        geoaddress_optionals = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": v.get("label", k),
            }
            for k, v in GEOADDRESS_FIELDS_OPTIONALS.items()
        }
        geoaddress_coordinates = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": v.get("label", k),
            }
            for k, v in GEOADDRESS_FIELDS_COORDINATES.items()
        }
        text_full = [data["value"] for data in geoaddress_data.values() if data["value"]]
        context = {
            "name": name,
            "value": value,
            "attrs": attrs,
            "search_value": ", ".join(text_full) if text_full else "",
            "autocomplete_url": autocomplete_url,
            "redirect_url": reverse(self.redirect_url),
            "geoaddress_data": geoaddress_data,
            "geoaddress_optionals": geoaddress_optionals,
            "geoaddress_coordinates": geoaddress_coordinates,
            "geoaddress_fields": list(GEOADDRESS_FULL_FIELDS.keys()),
        }
        return render_to_string(self.template_name, context)

    class Media:
        js = ("js/geoaddress_autocomplete.js",)
        css = {"all": ("css/geoaddress_autocomplete.css",)}


class GeoaddressField(models.JSONField):
    """Field to store geoaddress data via AddressModel with autocomplete."""

    def from_db_value(self, value: Any, _expression: Any, _connection: Any) -> GeoaddressValue | None:
        """Convert database value to GeoaddressValue."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = {}
        return GeoaddressValue(value) if isinstance(value, dict) else None

    def to_python(self, value: Any) -> GeoaddressValue | None:
        """Convert value to GeoaddressValue."""
        if value is None:
            return None
        if isinstance(value, GeoaddressValue):
            return value
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = {}
        return GeoaddressValue(value) if isinstance(value, dict) else None

    def get_prep_value(self, value: Any) -> dict | None:
        """Prepare value for database storage."""
        if value is None:
            return None
        if isinstance(value, GeoaddressValue):
            return dict(value)
        if isinstance(value, dict):
            return value
        return None

    def formfield(self, **kwargs: Any) -> Any:
        """Ensure the custom widget is used.

        Args:
            **kwargs: Additional arguments for formfield

        Returns:
            Form field with custom widget
        """
        defaults = {
            "widget": GeoaddressAutocompleteWidget,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)