"""Admin configuration for djgeoaddress."""

from .provider import ProviderAdmin
from .suggest import AddressAdmin
from .service import GeoaddressServiceAdmin

__all__ = ["ProviderAdmin", "AddressAdmin"]
