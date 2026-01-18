"""Manager for address suggestions."""

from typing import Any

from geoaddress.helpers import addresses_autocomplete
from virtualqueryset.managers import VirtualManager


class AddressManager(VirtualManager):
    """Manager for address suggestions from geoaddress."""

    _commands = {
        'addresses_autocomplete': addresses_autocomplete,
        'search': search_addresses,
        'reverse_geocode': reverse_geocode,
    }

    def __init__(self, query: str | None = None, **kwargs: Any):
        super().__init__()
        self.query = query
        self.first = kwargs.get("first", False)
        self.backend = kwargs.get("backend", None)
        self.attribute_search = kwargs.get("attribute_search", None)
        self._cached_data_autocomplete = None
        self._cached_data_search = None
        self._cached_data_reverse_geocode = None

    def set_cached_command(self, command: str, cache: Any) -> None:
        setattr(self, f"_cached_data_{command}", cache)
        return self.get_cached_command(command)

    def get_cached_command(self, command: str) -> Any:
        if getattr(self, f"_cached_data_{command}", None) is not None:
            return getattr(self, f"_cached_data_{command}")
        return None

    def get_command_data_list(self, results: Any) -> list[Any]:
        data_list = []
        for result in results:
            if isinstance(result, dict) and 'provider' in result:
                provider_obj = result['provider']
                normalize_data = provider_obj.get_service_normalize('addresses_autocomplete')  # type: ignore[attr-defined]
                if isinstance(normalize_data, list):
                    data_list.extend(normalize_data)
                else:
                    data_list.append(normalize_data)
        return data_list

    def get_command_data_dict(self, results: Any) -> dict[str, Any]:
        data_list = []
        for result in results:
            if isinstance(result, dict) and 'provider' in result:
                provider_obj = result['provider']
                normalize_data = provider_obj.get_service_normalize('addresses_autocomplete')  # type: ignore[attr-defined]
                if isinstance(normalize_data, list):
                    data_list.extend(normalize_data)
                else:
                    data_list.append(normalize_data)
        return data_list

    def get_queryset_command(self, command: str, **kwargs: Any) -> Any:
        cached = self.get_cached_command(command)
        if not cached:
            command_func = self._commands[command]
            results = command_func(**kwargs)
            data_list = []
            if isinstance(results, dict):
                data_list.extend(self.get_command_data_dict(results))
            elif isinstance(results, list):
                data_list.extend(self.get_command_data_list(results))
            cached = self.set_cached_command(command)
        return cached

    def get_data(self) -> list[Any]:
        if self._cached_data is not None:
            return self._cached_data

        if not self.query or not self.model:
            self._cached_data = []
            return self._cached_data

        try:
            kwargs = {}
            if self.backend:
                kwargs['attribute_search'] = {'name': self.backend}
            elif self.attribute_search:
                kwargs['attribute_search'] = self.attribute_search

            results = addresses_autocomplete(self.query, first=self.first, **kwargs)

            data_list = []
            if isinstance(results, dict):
                for provider_name, result in results.items():
                    if isinstance(result, dict) and 'provider' in result:
                        provider_obj = result['provider']
                        normalize_data = provider_obj.get_service_normalize('addresses_autocomplete')  # type: ignore[attr-defined]
                        if isinstance(normalize_data, list):
                            data_list.extend(normalize_data)
                        else:
                            data_list.append(normalize_data)
            elif isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'provider' in result:
                        provider_obj = result['provider']
                        normalize_data = provider_obj.get_service_normalize('addresses_autocomplete')  # type: ignore[attr-defined]
                        if isinstance(normalize_data, list):
                            data_list.extend(normalize_data)
                        else:
                            data_list.append(normalize_data)

            self._cached_data = data_list
            return self._cached_data
        except Exception:
            self._cached_data = []
            return self._cached_data

    def addresses_autocomplete(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        return self.get_queryset_command('addresses_autocomplete', query=query, first=first, **kwargs)

    def search_addresses(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        return self.get_queryset_command('search_addresses', query=query, first=first, **kwargs)

    def reverse_geocode(self, latitude: float, longitude: float, **kwargs: Any) -> Any:
        return self.get_queryset_command('reverse_geocode', latitude=latitude, longitude=longitude, **kwargs)

    def search(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        manager = AddressManager(query=query, first=first, **kwargs)
        manager.model = self.model
        return manager.get_queryset()
