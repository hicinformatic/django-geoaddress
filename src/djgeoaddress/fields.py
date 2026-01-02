from __future__ import annotations

import json
from typing import Any

from django.db import models
from django.forms.widgets import TextInput
from django.template.loader import render_to_string
from django.urls import reverse
from geoaddress import GEOADDRESS_FIELDS_ESSENTIALS


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
        context = {
            "name": name,
            "value": value,
            "attrs": attrs,
            "search_value": values.get("text") if isinstance(values, dict) else "",
            "autocomplete_url": autocomplete_url,
            "redirect_url": reverse(self.redirect_url),
            "geoaddress_data": {
                k: {
                    "value": values.get(k) or "" if isinstance(values, dict) else "",
                    "label": v,
                }
                for k, v in GEOADDRESS_FIELDS_ESSENTIALS.items()
            },
        }
        return render_to_string(self.template_name, context)

    class Media:
        js = ("js/geoaddress_autocomplete.js",)
        css = {"all": ("css/geoaddress_autocomplete.css",)}


class GeoaddressField(models.JSONField):
    """Field to store geoaddress data via AddressModel with autocomplete."""

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
