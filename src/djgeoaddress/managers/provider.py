"""Manager for geoaddress providers."""

from typing import Any

from geoaddress.helpers import get_address_providers
from virtualqueryset.managers import VirtualManager


class ProviderManager(VirtualManager):
    """Manager for geoaddress providers."""

    boolean_params = ["are_packages_installed", "are_services_implemented", "is_config_ready"]
    param_aliases = {
        "pkg": "are_packages_installed",
        "svc": "are_services_implemented",
        "cfg": "is_config_ready",
    }

    def __init__(self, **kwargs: Any):
        """Initialize manager with optional provider discovery options.

        Args:
            **kwargs: Arguments to pass to get_address_providers()
        """
        super().__init__()
        self.provider_kwargs = kwargs

    def search(self, query_string: str = "", **kwargs: Any) -> Any:
        """Search providers with query_string and optional filters.

        Args:
            query_string: Search query string
            **kwargs: Additional arguments (attribute_search, etc.)

        Returns:
            QuerySet with filtered providers
        """
        manager_kwargs = self.provider_kwargs.copy()
        if query_string:
            manager_kwargs["query_string"] = query_string
        if "attribute_search" in kwargs:
            manager_kwargs["attribute_search"] = kwargs["attribute_search"]
        manager_kwargs.update({k: v for k, v in kwargs.items() if k != "attribute_search"})

        search_manager = ProviderManager(**manager_kwargs)
        search_manager.model = self.model
        return search_manager.get_queryset()

    def get_data(self) -> list[Any]:
        """Get providers from geoaddress.

        Returns:
            List of ProviderModel instances
        """
        if not self.model:
            return []

        try:
            providers = get_address_providers(**self.provider_kwargs)
            provider_dicts = []
            if isinstance(providers, dict):
                for provider in providers.values():
                    provider_dicts.append(self._provider_to_dict(provider))
            elif isinstance(providers, list):
                provider_dicts = [self._provider_to_dict(p) for p in providers]
            else:
                return []

            objects = []
            for item in provider_dicts:
                if isinstance(item, dict):
                    # Get all model field names
                    model_field_names = {
                        field.name for field in self.model._meta.get_fields()
                    }
                    # Separate model fields from dynamic attributes
                    model_fields = {
                        k: v for k, v in item.items() if k in model_field_names
                    }
                    dynamic_attrs = {
                        k: v for k, v in item.items() if k not in model_field_names
                    }
                    # Create object with only model fields
                    obj = self.model(**model_fields)
                    # Set dynamic attributes after object creation
                    for attr_name, attr_value in dynamic_attrs.items():
                        setattr(obj, attr_name, attr_value)
                    objects.append(obj)
                elif isinstance(item, self.model):
                    objects.append(item)
            return objects
        except Exception:
            return []

    def _provider_to_dict(self, provider: Any) -> dict[str, Any]:
        """Convert provider object to dictionary.

        Args:
            provider: Provider object from geoaddress

        Returns:
            Dictionary representation of provider
        """
        if isinstance(provider, dict):
            return provider

        result = {}
        for param_name in self.boolean_params:
            result[param_name] = False
            if hasattr(provider, param_name):
                param_val = getattr(provider, param_name)
                if callable(param_val):
                    result[param_name] = param_val()
                else:
                    result[param_name] = bool(param_val)

        services = getattr(provider, "services", [])
        cost_data = {}
        for service in services:
            cost_attr = f"cost_{service}"
            if hasattr(provider, cost_attr):
                cost_val = getattr(provider, cost_attr)
                if callable(cost_val):
                    cost_data[cost_attr] = cost_val()
                else:
                    cost_data[cost_attr] = cost_val

        return {
            "name": getattr(provider, "name", ""),
            "display_name": getattr(provider, "display_name", ""),
            "description": getattr(provider, "description", ""),
            "required_packages": getattr(provider, "required_packages", []),
            "documentation_url": getattr(provider, "documentation_url", ""),
            "site_url": getattr(provider, "site_url", ""),
            "config_keys": getattr(provider, "config_keys", []),
            "config_required": getattr(provider, "config_required", []),
            "config_prefix": getattr(provider, "config_prefix", ""),
            "services": services,
            "missing_config_keys": getattr(provider, "missing_config_keys", []),
            "missing_services": getattr(provider, "missing_services", []),
            "missing_packages": getattr(provider, "missing_packages", []),
            **cost_data,
            **result,
        }
