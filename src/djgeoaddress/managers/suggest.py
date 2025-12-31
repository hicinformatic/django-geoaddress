"""Manager for address suggestions."""

from typing import Any

from geoaddress.helpers import search_addresses, get_address_by_reference
from virtualqueryset.managers import VirtualManager


class AddressManager(VirtualManager):
    """Manager for address suggestions from geoaddress."""
    backend: str | None = None
    first: bool = False

    def __init__(self, query: str | None = None, **kwargs: Any):
        """Initialize manager with optional query.

        Args:
            query: Search query string. If None, get_data() returns empty list.
            **kwargs: Additional arguments to pass to search_addresses()
        """
        super().__init__()
        self.query = query
        self.reference = kwargs.get("reference", None)
        self.search_kwargs = kwargs
        self.first = kwargs.get("first", False)
        self.backend = kwargs.get("backend", None)
        self.attribute_search = kwargs.get("attribute_search", None)
        self._cached_data = None

    def get_data(self) -> list[Any]:
        """Get address suggestions from geoaddress using search_addresses.

        Returns:
            List of AddressModel instances from geoaddress
        """
        if self._cached_data is not None:
            return self._cached_data

        if (not self.query and not self.reference) or not self.model:
            self._cached_data = []
            return self._cached_data

        try:
            if self.backend:
                self.attribute_search = {"name": self.backend}
            if self.reference:
                result = get_address_by_reference(self.reference, attribute_search=self.attribute_search)
            else:
                print("here", self.first)
                result = search_addresses(self.query, first=self.first, attribute_search=self.attribute_search)

            if isinstance(result, dict):
                results_list = []
                for provider_result in result.values():
                    if "result" in provider_result:
                        if isinstance(provider_result["result"], list):
                            results_list.extend(provider_result["result"])
                        else:
                            results_list.append(provider_result["result"])
                result = results_list

            if not isinstance(result, list):
                self._cached_data = []
                return self._cached_data

            objects = []
            for item in result:
                if isinstance(item, dict):
                    obj = self.model(**item)
                    objects.append(obj)
                elif isinstance(item, self.model):
                    objects.append(item)
            self._cached_data = objects
            return self._cached_data
        except Exception:
            self._cached_data = []
            return self._cached_data

    def search(self, query: str, first: bool = False, **kwargs: Any) -> Any:
        """Search addresses with a new query.

        Args:
            query: Search query string
            **kwargs: Additional arguments to pass to search_addresses()

        Returns:
            QuerySet with search results
        """
        manager = AddressManager(query=query, first=first, **kwargs)
        manager.model = self.model
        return manager.get_queryset()

