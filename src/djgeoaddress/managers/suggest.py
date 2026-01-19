"""Manager for address suggestions."""

from typing import Any

from geoaddress.helpers import addresses_autocomplete, search_addresses, reverse_geocode
from virtualqueryset.managers import VirtualManager


class AddressManager(VirtualManager):
    """Manager for address suggestions from geoaddress."""

    _commands = {
        'addresses_autocomplete': addresses_autocomplete,
        'search_addresses': search_addresses,
        'reverse_geocode': reverse_geocode,
    }

    def __init__(self, query: str | None = None, **kwargs: Any):
        super().__init__()
        self.query = query
        self.latitude = kwargs.get("latitude", None)
        self.longitude = kwargs.get("longitude", None)
        self.first = kwargs.get("first", False)
        self.backend = kwargs.get("backend", None)
        self.attribute_search = kwargs.get("attribute_search", None)
        self._command = kwargs.get("command", "search_addresses")
        self._cached_data_addresses_autocomplete = {}
        self._cached_data_search = {}
        self._cached_data_reverse_geocode = {}

    def _clear_cached_command(self, command: str) -> None:
        setattr(self, f"_cached_data_{command}", {})

    def set_cached_command(self, command: str, cache: Any, **kwargs: Any) -> Any:
        cache = self.queryset_class(model=self.model, data=cache)
        setattr(self, f"_cached_data_{command}", {"kwargs": kwargs, "data": cache})
        return self.get_cached_command(command, **kwargs)

    def get_cached_command(self, command: str, **kwargs: Any) -> Any:
        cache = getattr(self, f"_cached_data_{command}", {})
        if kwargs == cache.get("kwargs", {}) and cache.get("data") is not None:
            return cache.get("data")
        return None

    def get_command_data_list(self, results: Any, command: str) -> list[Any]:
        data_list = []
        for result in results:
            if isinstance(result, dict) and 'provider' in result:
                if "error" in result:
                    continue
                provider_obj = result['provider']
                normalize_data = provider_obj.get_service_normalize(command)  # type: ignore[attr-defined]
                if isinstance(normalize_data, list):
                    data_list.extend(normalize_data)
                else:
                    data_list.append(normalize_data)
        return data_list

    def get_command_data_list_from_dict(self, results: Any, command: str) -> list[Any]:
        data_list = []
        if isinstance(results, dict) and 'provider' in results:
            if "error" in results:
                return []
            provider_obj = results['provider']
            normalize_data = provider_obj.get_service_normalize(command)  # type: ignore[attr-defined]
            if isinstance(normalize_data, list):
                data_list.extend(normalize_data)
            else:
                data_list.append(normalize_data)
        return data_list

    def get_queryset_command(self, command: str, **kwargs: Any) -> Any:
        cached = self.get_cached_command(command)
        if not cached or kwargs.get("ignore_cache", False):
            self._clear_cached_command(command)
            command_func = self._commands[command]
            results = command_func(**kwargs)
            data_list = []
            if isinstance(results, dict):
                data_list.extend(self.get_command_data_list_from_dict(results, command))
            elif isinstance(results, list):
                data_list.extend(self.get_command_data_list(results, command))
            cached = self.set_cached_command(command, data_list, **kwargs)
        return cached

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

