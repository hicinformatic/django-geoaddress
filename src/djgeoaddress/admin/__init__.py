"""Admin configuration for djgeoaddress."""

from .provider import ProviderAdmin
from .suggest import AddressAdmin

__all__ = ["ProviderAdmin", "AddressAdmin"]
