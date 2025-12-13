"""Admin views for Django GeoAddress."""

from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_GET

try:
    from geoaddress.helpers import search_addresses
except ImportError:
    search_addresses = None


def _extract_backend_identifier(backend_display: str) -> str:
    """Extract backend identifier from display name.
    
    Maps display names to identifiers:
    - "OpenStreetMap Nominatim" -> "nominatim"
    - "Photon" -> "photon"
    - etc.
    """
    if not backend_display:
        return ""
    
    backend_lower = backend_display.lower().strip()
    
    # Map common display names to identifiers
    backend_map = {
        "openstreetmap nominatim": "nominatim",
        "nominatim": "nominatim",
        "photon": "photon",
        "google maps": "google_maps",
        "here": "here",
        "mapbox": "mapbox",
        "opencage": "opencage",
        "locationiq": "locationiq",
        "geocode earth": "geocode_earth",
        "maps.co": "maps_co",
        "maps co": "maps_co",
        "geoapify": "geoapify",
    }
    
    # Check exact match first
    if backend_lower in backend_map:
        return backend_map[backend_lower]
    
    # Check if it contains any of the mapped names
    for display_name, identifier in backend_map.items():
        if display_name in backend_lower or backend_lower in display_name:
            return identifier
    
    # Try to extract from display name
    # Remove common prefixes
    backend_id = backend_lower.replace("openstreetmap ", "").replace("openstreetmap_", "")
    # Replace spaces with underscores
    backend_id = backend_id.replace(" ", "_").strip("_")
    
    # If still empty or just underscores, try to get the last word
    if not backend_id or backend_id == "_":
        words = backend_lower.split()
        if words:
            backend_id = words[-1]  # Take last word
    
    # Final check: if backend_id is still empty or just whitespace, return empty string
    if not backend_id or not backend_id.strip():
        return ""
    
    return backend_id.strip()


@require_GET
def address_autocomplete_admin_view(request):
    """Admin address autocomplete view for AddressField widgets."""
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})
    
    if not search_addresses:
        return JsonResponse(
            {"error": "geoaddress.helpers not available", "results": []},
            status=503,
        )
    
    backends_config = getattr(settings, "GEOADDRESS_BACKENDS", None)
    if not backends_config:
        return JsonResponse(
            {"error": "No address backends configured", "results": []},
            status=503,
        )
    
    country = request.GET.get("country")
    backend = request.GET.get("backend")
    limit = int(request.GET.get("limit", 10))
    min_confidence = request.GET.get("min_confidence")
    min_confidence_float = float(min_confidence) if min_confidence else None
    
    try:
        search_result = search_addresses(
            backends_config=backends_config,
            query=query,
            country=country,
            backend=backend,
            limit=limit,
            min_confidence=min_confidence_float,
        )
        results = search_result.get("results", [])
        # Results are already standardized by search_addresses
        # Add id and admin_url to each result
        formatted_results = []
        for addr in results:
            # Build id from backend and reference
            backend_display = addr.get("backend") or ""
            reference = addr.get("reference")
            addr_id = None
            backend_id = None
            
            if reference and backend_display:
                backend_id = _extract_backend_identifier(backend_display)
                # Ensure backend_id is not empty
                if backend_id and backend_id.strip() and reference:
                    addr_id = f"{backend_id}-{reference}"
            
            # If we still don't have an id, try to use the reference directly
            if not addr_id and reference:
                # Try to extract backend from other fields
                backend_used = addr.get("backend_used") or ""
                if backend_used:
                    backend_id = _extract_backend_identifier(backend_used)
                    if backend_id and backend_id.strip():
                        addr_id = f"{backend_id}-{reference}"
            
            if not addr_id:
                # Fallback to text as id
                addr_id = addr.get("text", "") or ""
            
            # Generate admin_url using AddressField.get_admin_url
            admin_url = None
            if reference and backend_id and backend_id.strip():
                try:
                    from ..fields import AddressField
                    # Build address data dict for get_admin_url
                    address_data = {
                        "backend_used": backend_id,
                        "backend_reference": reference,
                        "backend": backend_id,
                        "address_reference": reference,
                    }
                    admin_url = AddressField.get_admin_url(address_data)
                except Exception:
                    admin_url = None
            
            formatted_result = dict(addr)
            formatted_result["id"] = addr_id
            formatted_result["admin_url"] = admin_url
            formatted_results.append(formatted_result)
        return JsonResponse({"results": formatted_results})
    except Exception as exc:
        return JsonResponse(
            {"error": f"Address search failed: {str(exc)}", "results": []},
            status=500,
        )


def get_admin_urls():
    return [
        path(
            "address/autocomplete/",
            admin.site.admin_view(address_autocomplete_admin_view),
            name="geoaddress_address_autocomplete",
        ),
    ]


__all__ = [
    "address_autocomplete_admin_view",
    "get_admin_urls",
]
