"""Manager for address suggestions."""

from typing import Any

from geoaddress.helpers import addresses_autocomplete, search_addresses, reverse_geocode
from djproviderkit.managers import BaseServiceProviderManager

class AddressManager(BaseServiceProviderManager):
    """Manager for address suggestions from geoaddress."""

    _commands = {
        'addresses_autocomplete': addresses_autocomplete,
        'search_addresses': search_addresses,
        'reverse_geocode': reverse_geocode,
    }

    _args_available = ["query", "latitude", "longitude", "first", "backend", "attribute_search"]
    _default_command = "search_addresses"

    def addresses_autocomplete(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        return self.get_queryset_command('addresses_autocomplete', query=query, first=first, **kwargs)

    def search_addresses(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        return self.get_queryset_command('search_addresses', query=query, first=first, **kwargs)

    def reverse_geocode(self, geoaddress_id: str, **kwargs: Any) -> Any:
        geoaddress_id_parts = geoaddress_id.split("_")
        attr = {"name": "_".join(geoaddress_id_parts[:-1])}
        lat, lon = geoaddress_id_parts[-1].split(":")
        return self.get_queryset_command('reverse_geocode', latitude=lat, attribute_search=attr, longitude=lon, ignore_cache=True, **kwargs)

    def get_data(self) -> Any:
        command = self._command
        kwargs = {
            "query": self.query,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "backend": self.backend,
            "attribute_search": self.attribute_search,
            "first": self.first,
        }
        return self.get_queryset_command(command, **kwargs)

