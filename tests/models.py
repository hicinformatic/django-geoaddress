"""Test models for django-geoaddress."""

from django.db import models
from djgeoaddress.fields import AddressField


class TestLocation(models.Model):
    """Test model to demonstrate AddressField usage."""
    
    name = models.CharField(max_length=200, help_text="Location name")
    address = AddressField(help_text="Full address with geocoding")
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Test Location"
        verbose_name_plural = "Test Locations"
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name or "Unnamed location"

