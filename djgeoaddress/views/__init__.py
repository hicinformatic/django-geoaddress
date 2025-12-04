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
        min_confidence (optional): Minimum confidence score (0.0-1.0)
        
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
