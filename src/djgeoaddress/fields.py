from django.db import models
from django.forms.widgets import TextInput

from djgeoaddress.models.suggest import AddressModel
from django.urls import reverse
from geoaddress import GEOADDRESS_FIELDS_ESSENTIALS
from django.template.loader import render_to_string


class GeoaddressAutocompleteWidget(TextInput):
    """Widget to store geoaddress data via AddressModel with autocomplete."""
    address_url_name = "djgeoaddress:search_addresses"
    template_name = "djgeoaddress/autocomplete.html"

    def get_url(self):
        """Return the autocomplete URL."""
        return reverse(self.address_url_name)

    def render(self, name, value, attrs=None, renderer=None):
        autocomplete_url = self.get_url()
        context = {
            'name': name,
            'value': value,
            'attrs': attrs,
            'autocomplete_url': autocomplete_url,
            'geoaddress_fields': GEOADDRESS_FIELDS_ESSENTIALS,
        }
        return render_to_string(self.template_name, context)

    class Media:
        js = ('js/geoaddress_autocomplete.js',)
        css = {
            'all': ('css/geoaddress_autocomplete.css',)
        }


class GeoaddressField(models.JSONField):
    """Field to store geoaddress data via AddressModel with autocomplete."""
    default = {}
    
    def formfield(self, **kwargs):
        """Ensure the custom widget is used."""
        defaults = {
            'widget': GeoaddressAutocompleteWidget,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
