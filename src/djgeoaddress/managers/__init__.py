"""Managers for djgeoaddress."""

from .provider import ProviderManager
from .suggest import AddressManager

__all__ = ["AddressManager", "ProviderManager"]
