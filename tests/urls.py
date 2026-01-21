"""URL configuration for testing django-geoaddress."""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from tests.app.viewsets import LocationViewSet

router = DefaultRouter()
router.register(r"api/locations", LocationViewSet, basename="location")

urlpatterns = [
    path("", RedirectView.as_view(url="/locations/", permanent=False)),
    path("admin/", admin.site.urls),
    path("djgeoaddress/", include("djgeoaddress.urls")),
    path("locations/", include("tests.app.urls")),
    path("", include(router.urls)),
]

# admin.site.site_header = "Django GeoAddress - Administration"
# admin.site.site_title = "Django GeoAddress Admin"
# admin.site.index_title = "Welcome to Django GeoAddress"
