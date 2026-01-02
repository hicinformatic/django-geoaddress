from django.db import models
from django.forms.widgets import TextInput

from djgeoaddress.models.suggest import AddressModel
from django.urls import reverse
from geoaddress import GEOADDRESS_FIELDS_ESSENTIALS
from django.template.loader import render_to_string
import json

class GeoaddressAutocompleteWidget(TextInput):
    """Widget to store geoaddress data via AddressModel with autocomplete."""
    address_url_name = "djgeoaddress:search_addresses"
    template_name = "djgeoaddress/autocomplete.html"
    redirect_url = "djgeoaddress:redirect_to_address"

    def get_url(self):
        """Return the autocomplete URL."""
        return reverse(self.address_url_name)

    def render(self, name, value, attrs=None, renderer=None):
        autocomplete_url = self.get_url()
        values = json.loads(value)
        context = {
            'name': name,
            'value': value,
            'attrs': attrs,
            'search_value': values.get('text'),
            'autocomplete_url': autocomplete_url,
            'redirect_url': reverse(self.redirect_url),
            'geoaddress_data': {
                k: {
                    "value":values.get(k) or '',
                    "label": v,
                } for k, v in GEOADDRESS_FIELDS_ESSENTIALS.items()}
        }
        return render_to_string(self.template_name, context)

    class Media:
        js = ('js/geoaddress_autocomplete.js',)
        css = {
            'all': ('css/geoaddress_autocomplete.css',)
        }


class GeoaddressField(models.JSONField):
    """Field to store geoaddress data via AddressModel with autocomplete."""
    
    def formfield(self, **kwargs):
        """Ensure the custom widget is used."""
        defaults = {
            'widget': GeoaddressAutocompleteWidget,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
