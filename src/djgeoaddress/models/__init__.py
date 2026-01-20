"""Models for djgeoaddress."""

from .provider import GeoaddressProviderModel
from .suggest import AddressModel, BaseAddressModel

__all__ = ["AddressModel", "BaseAddressModel", "GeoaddressProviderModel"]
