"""Models for djgeoaddress."""

from .provider import ProviderModel
from .suggest import AddressModel, BaseAddressModel

__all__ = ["AddressModel", "BaseAddressModel", "ProviderModel"]
