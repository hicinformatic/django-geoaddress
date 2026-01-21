"""URL configuration for tests.app."""

from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    path("", views.LocationListView.as_view(), name="location_list"),
    path("create/", views.LocationCreateView.as_view(), name="location_create"),
    path("<int:pk>/", views.LocationDetailView.as_view(), name="location_detail"),
    path("<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    path("<int:pk>/delete/", views.LocationDeleteView.as_view(), name="location_delete"),
]
