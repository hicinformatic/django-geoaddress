"""Manager for geoaddress providers."""

from djproviderkit.managers import BaseProviderManager


class ProviderManager(BaseProviderManager):
    """Manager for geoaddress providers."""
    package_name = 'geoaddress'