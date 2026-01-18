"""Django GeoAddress - Address verification and geocoding for Django."""

from __future__ import annotations

from django.db import models

__version__ = "0.1.3"

default_app_config = "djgeoaddress.apps.DjGeoAddressConfig"

fields_associations = {
    'int': models.IntegerField,
    'float': models.FloatField,
    'bool': models.BooleanField,
    'list': models.JSONField,
    'str': models.CharField,
    'text': models.TextField,
    'date': models.DateField,
    'time': models.TimeField,
    'datetime': models.DateTimeField,
    'email': models.EmailField,
    'url': models.URLField,
}
