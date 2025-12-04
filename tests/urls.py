"""URL configuration for testing django-geoaddress."""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("djgeoaddress/", include("djgeoaddress.urls")),
]

admin.site.site_header = "Django GeoAddress - Administration"
admin.site.site_title = "Django GeoAddress Admin"
admin.site.index_title = "Welcome to Django GeoAddress"

