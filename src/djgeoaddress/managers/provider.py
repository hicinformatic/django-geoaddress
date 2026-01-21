"""Manager for geoaddress providers."""

from typing import Any

from djproviderkit.managers import BaseProviderManager
from geoaddress.helpers import get_address_providers


class ProviderManager(BaseProviderManager):
    """Manager for geoaddress providers."""
    package_name = 'geoaddress'