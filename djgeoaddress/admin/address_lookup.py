"""Admin for address suggestions and lookup."""

from __future__ import annotations

import json
from typing import Optional

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models.address_lookup import AddressLookup, AddressLookupQuerySet
from .address_backend import BackendFilter, get_backend_configs

try:
    from geoaddress.helpers import (
        GEOADDRESS_FIELDS_NORMALIZED,
        get_address_by_reference as get_address_by_reference_fn,
        search_addresses as search_addresses_fn,
    )
except ImportError:
    GEOADDRESS_FIELDS_NORMALIZED = {}
    search_addresses_fn = None
    get_address_by_reference_fn = None


@admin.register(AddressLookup)
class AddressLookupAdmin(admin.ModelAdmin):
    """Simplified admin for address lookup using search_addresses."""

    list_display = ["reference_display", "text_display", "relevance_display", "confidence_display", "backend_display"]
    search_fields = ["label"]
    ordering = []
    list_per_page = 20
    list_display_links = ("reference_display",)
    list_filter = [BackendFilter]
    
    # Will be populated dynamically from GEOADDRESS_FIELDS_NORMALIZED
    readonly_fields = []
    fieldsets = None

    def get_queryset(self, request: HttpRequest) -> AddressLookupQuerySet:
        """Get queryset by calling search_addresses with query parameter."""
        if not search_addresses_fn:
            return AddressLookupQuerySet(model=AddressLookup, data=[])

        # Get search query from request
        query = request.GET.get("q", "").strip()
        if not query:
            return AddressLookupQuerySet(model=AddressLookup, data=[])

        # Get backend filter if any
        backend = request.GET.get("backend", "").strip() or None

        # Get backend configs
        config_list = get_backend_configs()
        if not config_list:
            return AddressLookupQuerySet(model=AddressLookup, data=[])

        # Call search_addresses
        try:
            search_result = search_addresses_fn(
                backends_config=config_list,
                query=query,
                backend=backend,
                limit=100,
            )
        except Exception:
            return AddressLookupQuerySet(model=AddressLookup, data=[])

        # Convert results to AddressLookup objects
        results = search_result.get("results", [])
        objects = []
        for result in results:
            # Use the normalized payload directly
            payload = result.copy()
            
            # Create AddressLookup object
            geoaddress_id = payload.get("geoaddress_id")
            obj = AddressLookup(
                label=payload.get("text", ""),
                backend_used=payload.get("backend_name", ""),
                backend_reference=payload.get("reference", ""),
                raw_payload=payload,
            )
            # Use geoaddress_id as pk for detail view
            if geoaddress_id:
                obj.pk = geoaddress_id
            objects.append(obj)

        return AddressLookupQuerySet(model=AddressLookup, data=objects)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable add permission."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Optional[AddressLookup] = None) -> bool:
        """Disable change permission."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[AddressLookup] = None) -> bool:
        """Disable delete permission."""
        return False

    def get_object(self, request: HttpRequest, object_id: Optional[str], from_field: Optional[str] = None) -> Optional[AddressLookup]:
        """Get object by calling get_address_by_reference with geoaddress_id."""
        if not object_id or not get_address_by_reference_fn:
            return None
        
        # Parse geoaddress_id format: "backend_name-reference"
        parts = object_id.split("-", 1)
        if len(parts) != 2:
            return None
        
        backend_name, reference = parts
        
        # Get backend configs
        config_list = get_backend_configs()
        if not config_list:
            return None
        
        # Fetch from backend
        try:
            payload = get_address_by_reference_fn(
                backends_config=config_list,
                backend=backend_name,
                address_reference=reference,
            )
        except Exception:
            return None
        
        if not payload or payload.get("error"):
            return None
        
        # Create AddressLookup object from payload
        geoaddress_id = payload.get("geoaddress_id")
        obj = AddressLookup(
            label=payload.get("text", ""),
            backend_used=payload.get("backend_name", ""),
            backend_reference=payload.get("reference", ""),
            raw_payload=payload,
        )
        if geoaddress_id:
            obj.pk = geoaddress_id
        
        return obj

    @admin.display(description=_("Raw payload"))
    def raw_payload_display(self, obj: AddressLookup) -> str:
        """Display raw payload as JSON."""
        if not obj.raw_payload:
            return "—"
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="background: #f8f9fa; padding: 1rem; border-radius: 0.25rem; color: #212529; overflow-x: auto;">{}</pre>',
            payload,
        )


# Generate display methods dynamically from GEOADDRESS_FIELDS_NORMALIZED
if GEOADDRESS_FIELDS_NORMALIZED:
    # Build readonly_fields and fieldsets for detail view
    readonly_fields_list = [f"{f}_display" for f in GEOADDRESS_FIELDS_NORMALIZED.keys()]
    readonly_fields_list.append("raw_payload_display")
    
    fieldsets_list = [
        (None, {"fields": readonly_fields_list[:-1]}),  # All normalized fields
        (_("Raw payload"), {"fields": ("raw_payload_display",), "classes": ("collapse",)}),
    ]
    
    # Set readonly_fields and fieldsets
    AddressLookupAdmin.readonly_fields = readonly_fields_list
    AddressLookupAdmin.fieldsets = tuple(fieldsets_list)
    
    # Generate display methods
    for field_name, description in GEOADDRESS_FIELDS_NORMALIZED.items():
        def _make_display_method(field: str = field_name, desc: str = description):
            @admin.display(description=_(desc), ordering=field)
            def display_method(self, obj: AddressLookup):
                if not obj.raw_payload:
                    return "—"
                value = obj.raw_payload.get(field)
                if value is None:
                    return "—"
                if field in ("latitude", "longitude") and isinstance(value, (int, float)):
                    return f"{float(value):.6f}"
                if field in ("confidence", "relevance") and isinstance(value, (int, float)):
                    return f"{float(value):.1f}%"
                return str(value)
            
            display_method.__name__ = f"{field}_display"
            return display_method
        
        method = _make_display_method()
        setattr(AddressLookupAdmin, f"{field_name}_display", method)


__all__ = [
    "AddressLookupAdmin",
]
