"""Views for djgeoaddress."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..address_backends import build_address_backends_payload

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


__all__ = [
    "address_backends_status_view",
    "address_autocomplete_view",
]


@require_GET
def address_backends_status_view(request):
    """JSON diagnostics endpoint for address backends.
    
    Returns status and capabilities of configured address backends.
    Supports testing with custom address data via query parameters.
    
    Query parameters:
        operation (optional): Operation to test (default: "validate")
        address_line1, address_line2, address_line3: Address lines
        city, postal_code, state, country: Address components
        latitude, longitude: Coordinates for reverse geocoding
    """
    backends_config = getattr(settings, "GEOADDRESS_BACKENDS", None)
    if not backends_config:
        return JsonResponse(
            {"error": "No address backends configured"},
            status=503,
        )
    
    operation = request.GET.get("operation", "validate")
    address_kwargs = {
        "address_line1": request.GET.get("address_line1"),
        "address_line2": request.GET.get("address_line2"),
        "address_line3": request.GET.get("address_line3"),
        "city": request.GET.get("city"),
        "postal_code": request.GET.get("postal_code"),
        "state": request.GET.get("state"),
        "country": request.GET.get("country"),
    }
    address_kwargs = {k: v for k, v in address_kwargs.items() if v}
    
    extra_kwargs = {}
    if request.GET.get("latitude"):
        try:
            extra_kwargs["latitude"] = float(request.GET.get("latitude"))
        except (TypeError, ValueError):
            pass
    if request.GET.get("longitude"):
        try:
            extra_kwargs["longitude"] = float(request.GET.get("longitude"))
        except (TypeError, ValueError):
            pass
    
    payload = build_address_backends_payload(
        backends_config=backends_config,
        operation=operation,
        address_kwargs=address_kwargs if address_kwargs else None,
        extra_kwargs=extra_kwargs if extra_kwargs else None,
    )
    
    return JsonResponse(payload, json_dumps_params={"indent": 2})


@require_GET
def _address_autocomplete_view_impl(request):
    """Implementation of address autocomplete API endpoint.
    
    Query parameters:
        q (required): Search query string
        country (optional): ISO country code to filter results
        backend (optional): Specific backend name to use
        limit (optional): Maximum number of results (default: 10)
        min_confidence (optional): Minimum confidence score (0.0-1.0, converted to percentage internally)
        
    Returns:
        JSON response with search results
    """
    view_enabled = getattr(settings, "GEOADDRESS_VIEW_ENABLE", False)
    if not view_enabled:
        return JsonResponse(
            {"error": "Address autocomplete view is disabled"}, status=403
        )
    
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})
    
    if not search_addresses:
        return JsonResponse(
            {"error": "geoaddress.helpers not available"},
            status=503,
        )
    
    backends_config = getattr(settings, "GEOADDRESS_BACKENDS", None)
    if not backends_config:
        return JsonResponse(
            {"error": "No address backends configured"},
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
        
        # Add id and admin_url to each result
        results = search_result.get("results", [])
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
        
        search_result["results"] = formatted_results
        return JsonResponse(search_result)
    except Exception as exc:
        return JsonResponse(
            {"error": f"Address search failed: {str(exc)}"},
            status=500,
        )


def address_autocomplete_view(request):
    """Public API endpoint for address autocomplete.
    
    Can be protected with authentication based on settings.
    """
    view_func = _address_autocomplete_view_impl
    auth_required = getattr(settings, "GEOADDRESS_VIEW_AUTH_ENABLE", False)
    if auth_required:
        view_func = login_required(view_func)
    return view_func(request)
