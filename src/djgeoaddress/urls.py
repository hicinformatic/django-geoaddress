"""URL configuration for django-geoaddress."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path

from .views.provider import list_providers
from .views.suggest import search_addresses

app_name = "djgeoaddress"

urlpatterns = [
    path("providers/", list_providers, name="list_providers"),
    path("addresses/", search_addresses, name="search_addresses"),
]
