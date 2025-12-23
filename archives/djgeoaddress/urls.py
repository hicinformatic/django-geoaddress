"""URL configuration for djgeoaddress app."""

from django.urls import path
from .views import address_backends_status_view, address_autocomplete_view

app_name = "djgeoaddress"

urlpatterns = [
    # Address backend diagnostics (JSON endpoint)
    path(
        "diagnostics/address-backends/",
        address_backends_status_view,
        name="address-backends-status",
    ),
    # Address autocomplete
    path(
        "address/autocomplete/",
        address_autocomplete_view,
        name="address-autocomplete",
    ),
]
