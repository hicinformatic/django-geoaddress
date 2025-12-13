"""Admin for djgeoaddress."""

from django.contrib import admin

from .address_backend import AddressBackendInfoAdmin
from .views import get_admin_urls

# Extend admin site URLs with custom autocomplete endpoint
_original_get_urls = admin.site.get_urls


def _get_urls_with_autocomplete():
    """Add autocomplete URL to admin site."""
    custom_urls = get_admin_urls()
    original_urls = _original_get_urls()
    return custom_urls + original_urls


admin.site.get_urls = _get_urls_with_autocomplete  # type: ignore[method-assign]

__all__ = [
    "AddressBackendInfoAdmin",
]
