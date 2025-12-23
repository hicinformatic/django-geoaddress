"""Manager for address suggestions."""

from typing import Any

from providerkit.helpers import try_providers_first
from virtualqueryset.managers import VirtualManager


class AddressManager(VirtualManager):
    """Manager for address suggestions from geoaddress."""

    def __init__(self, query: str | None = None, **kwargs: Any):
        """Initialize manager with optional query.

        Args:
            query: Search query string. If None, get_data() returns empty list.
            **kwargs: Additional arguments to pass to try_providers_first()
        """
        super().__init__()
        self.query = query
        self.search_kwargs = kwargs

    def get_data(self) -> list[dict[str, Any]]:
        """Get address suggestions from geoaddress using try_providers_first.

        Returns:
            List of address dictionaries from geoaddress
        """
        if not self.query:
            return []

        try:
            additional_args = {"query": self.query}
            additional_args.update(self.search_kwargs)
            
            provider_kwargs = {
                "lib_name": "geoaddress",
            }
            for key in ["json", "config", "dir_path", "base_module", "query_string", "search_fields"]:
                if key in self.search_kwargs:
                    provider_kwargs[key] = self.search_kwargs[key]
            
            result = try_providers_first(
                command="search_addresses",
                additional_args=additional_args,
                **provider_kwargs,
            )
            if isinstance(result, list):
                return result
            return []
        except Exception:
            return []

    def search(self, query: str, **kwargs: Any) -> Any:
        """Search addresses with a new query.

        Args:
            query: Search query string
            **kwargs: Additional arguments to pass to try_providers_first()

        Returns:
            QuerySet with search results
        """
        manager = AddressManager(query=query, **kwargs)
        manager.model = self.model
        return manager.get_queryset()

