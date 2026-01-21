"""Viewsets for tests.app."""

from rest_framework import viewsets

from .models import Location
from .serializers import LocationSerializer
from django_boosted.rest_framework import BoostedRestFrameworkMetadata


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for Location model."""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    metadata_class = BoostedRestFrameworkMetadata