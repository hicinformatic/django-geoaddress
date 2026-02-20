"""Admin for tests.app."""

from django.contrib import admin

from .models import Addressbook, Location



@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Admin for Location model."""

    list_display = ["name", "address_display", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["name", "address"],
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

class LocationInline(admin.TabularInline):
    """Inline for Location model."""
    model = Location
    extra = 0
    fields = ["name", "address", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Addressbook)
class AddressbookAdmin(admin.ModelAdmin):
    """Admin for Addressbook model."""
    list_display = ["name"]
    search_fields = ["name"]
    inlines = [LocationInline]