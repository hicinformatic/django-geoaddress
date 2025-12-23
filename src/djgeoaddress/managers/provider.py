"""Manager for geoaddress providers."""

from typing import Any

from geoaddress.helpers import get_address_providers
from virtualqueryset.managers import VirtualManager


class ProviderManager(VirtualManager):
    """Manager for geoaddress providers."""

    def __init__(self, **kwargs: Any):
        """Initialize manager with optional provider discovery options.

        Args:
            **kwargs: Arguments to pass to get_address_providers()
        """
        super().__init__()
        self.provider_kwargs = kwargs

    def get_data(self) -> list[dict[str, Any]]:
        """Get providers from geoaddress.

        Returns:
            List of provider dictionaries
        """
        try:
            providers = get_address_providers(**self.provider_kwargs)
            if isinstance(providers, dict):
                result = []
                for provider in providers.values():
                    result.append(self._provider_to_dict(provider))
                return result
            if isinstance(providers, list):
                return [self._provider_to_dict(p) for p in providers]
            return []
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

        is_available = False
        is_configured = False
        if hasattr(provider, "is_available"):
            is_available_val = provider.is_available
            if callable(is_available_val):
                is_available = is_available_val()
            else:
                is_available = bool(is_available_val)

        if hasattr(provider, "is_configured"):
            is_configured_val = provider.is_configured
            if callable(is_configured_val):
                is_configured = is_configured_val()
            else:
                is_configured = bool(is_configured_val)

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
            "services": getattr(provider, "services", []),
            "is_available": is_available,
            "is_configured": is_configured,
        }

