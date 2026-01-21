"""Serializers for tests.app."""

from rest_framework import serializers
from .models import Location
from djgeoaddress.rest_framework import AddressField

class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model."""
    address = AddressField()
    address_display = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ["id", "name", "address", "address_display", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_address_display(self, obj: Location) -> str:
        """Return formatted address string."""
        if obj.address:
            return str(obj.address)
        return ""
