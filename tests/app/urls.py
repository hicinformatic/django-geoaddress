"""URL configuration for tests.app."""

from django.urls import path

from . import views

app_name = "app"

urlpatterns = [
    # Choice view
    path("", views.LocationChoiceView.as_view(), name="location_choice"),
    # Original views
    path("original/", views.LocationListView.as_view(), name="location_list"),
    path("create/", views.LocationCreateView.as_view(), name="location_create"),
    path("<int:pk>/", views.LocationDetailView.as_view(), name="location_detail"),
    path("<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    path("<int:pk>/delete/", views.LocationDeleteView.as_view(), name="location_delete"),
    # Django native views
    path("django/", views.LocationDjangoListView.as_view(), name="location_django_list"),
    path("django/<int:pk>/edit/", views.LocationDjangoUpdateView.as_view(), name="location_django_update"),
    path("django/<int:pk>/remove/", views.LocationDjangoRemoveView.as_view(), name="location_django_remove"),
    # REST Framework views
    path("rest/", views.LocationRestListView.as_view(), name="location_rest_list"),
    path("rest/create/", views.LocationRestCreateView.as_view(), name="location_rest_create"),
    path("rest/<int:pk>/edit/", views.LocationRestUpdateView.as_view(), name="location_rest_update"),
    path("rest/<int:pk>/remove/", views.LocationRestRemoveView.as_view(), name="location_rest_remove"),
]
