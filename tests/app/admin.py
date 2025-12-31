"""Admin for tests.app."""

from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin for Location model."""

    list_display = ["name", "provider", "address_display", "created_at", "updated_at"]
    list_filter = ["provider", "created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["provider",]
    fieldsets = [
        (None, {
            "fields": ["name", "provider", "address"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
        }),
    ]

    def address_display(self, obj):
        """Display address text."""
        if obj.address and obj.address.get("text"):
            return obj.address["text"]
        return "-"
    
    address_display.short_description = "Address"

