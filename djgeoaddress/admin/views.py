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
        formatted_results = [
            {
                "id": addr.get("formatted", ""),  # Use formatted address as ID
                "text": addr.get("formatted", ""),  # Display formatted address
                **addr  # Include all address components
            }
            for addr in results
        ]
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
