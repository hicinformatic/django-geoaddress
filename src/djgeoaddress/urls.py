"""URL configuration for django-geoaddress."""

from django.urls import path

from .views.provider import list_providers, detail_provider
from .views.suggest import (
    search_addresses,
    detail_address,
    redirect_to_address_list,
    redirect_to_address,
)
from .views.index import index

app_name = "djgeoaddress"

urlpatterns = [
    path("", index, name="index"),
    path("providers/<str:provider_name>/", detail_provider, name="detail_provider"),
    path("providers/", list_providers, name="list_providers"),
    path("suggest/redirect-to-address-list/", redirect_to_address_list, name="redirect_to_address_list"),
    path("suggest/redirect-to-address/", redirect_to_address, name="redirect_to_address"),
    path("suggest/<str:geoaddress_id>/", detail_address, name="detail_address"),
    path("suggest/", search_addresses, name="search_addresses"),
]
