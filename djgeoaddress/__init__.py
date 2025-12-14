"""Django GeoAddress - Address verification and geocoding for Django."""

from __future__ import annotations

__version__ = "0.1.0"

default_app_config = "djgeoaddress.apps.DjGeoAddressConfig"

# Fields can be imported safely
from .fields import (  # noqa: E402, F401
    AddressAutocompleteFormField,
    AddressAutocompleteWidget,
    AddressField,
    AddressFormField,
    AddressWidget,
)

__all__ = [
    "AddressField",
    "AddressFormField",
    "AddressWidget",
    "AddressAutocompleteWidget",
    "AddressAutocompleteFormField",
]

# Models should NOT be imported at module level (Django not ready yet)
# Import them as: from djgeoaddress.models import AddressBackendInfo
