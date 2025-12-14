"""Django app configuration."""

from django.apps import AppConfig


class DjGeoAddressConfig(AppConfig):
    """Configuration for the djgeoaddress app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "djgeoaddress"
    verbose_name = "GeoAddress"
