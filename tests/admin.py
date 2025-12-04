"""Admin for test models."""

from django.contrib import admin
from .models import TestLocation


@admin.register(TestLocation)
class TestLocationAdmin(admin.ModelAdmin):
    """Admin for TestLocation model to demonstrate AddressField."""
    
    list_display = ["name", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "notes"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (None, {
            "fields": ("name", "address", "notes"),
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

