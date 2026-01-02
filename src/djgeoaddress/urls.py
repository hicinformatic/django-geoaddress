"""URL configuration for django-geoaddress."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path

from .views.provider import list_providers, detail_provider
from .views.suggest import search_addresses, redirect_to_address, detail_address

app_name = "djgeoaddress"

urlpatterns = [
    path("providers/", list_providers, name="list_providers"),
    path("providers/<str:provider_name>/", detail_provider, name="detail_provider"),
    path("suggest/", search_addresses, name="search_addresses"),
    path("suggest/redirect-to-address/", redirect_to_address, name="redirect_to_address"),
    path("suggest/<str:geoaddress_id>/", detail_address, name="detail_address"),
]
