"""Views for address suggestions."""

from django.http import JsonResponse
from django.shortcuts import render

from ..managers.suggest import AddressManager
from ..models.provider import ProviderModel
from ..models.suggest import AddressModel


def search_addresses(request):
    """Search addresses with filters.
    
    Query parameters:
        - q: Search query string
        - bck: Backend name filter
        - first: Return first result only (1 or 0)
        - format: Response format ('html' or 'json', default: 'html')
    
    Returns:
        HTML or JSON response with address suggestions
    """
    format_type = request.GET.get("format", "html")
    query = request.GET.get("q", "").strip()
    backend = request.GET.get("bck", "").strip() or None
    first_param = request.GET.get("first", "")
    first = first_param == "1" if first_param else False
    
    # Prepare manager kwargs
    kwargs = {}
    if backend:
        kwargs["backend"] = backend
    if first:
        kwargs["first"] = first
    
    # Get addresses using AddressManager
    manager = AddressManager(query=query if query else None, **kwargs)
    manager.model = AddressModel
    addresses = manager.get_queryset()
    
    # Convert to list of dicts for JSON response
    result = []
    for address in addresses:
        address_data = {
            "text": address.text,
            "reference": address.reference,
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "address_line3": address.address_line3,
            "city": address.city,
            "postal_code": address.postal_code,
            "state": address.state,
            "region": address.region,
            "country": address.country,
            "country_code": address.country_code,
            "municipality": address.municipality,
            "neighbourhood": address.neighbourhood,
            "address_type": address.address_type,
            "latitude": address.latitude,
            "longitude": address.longitude,
            "osm_id": address.osm_id,
            "osm_type": address.osm_type,
            "confidence": address.confidence,
            "relevance": address.relevance,
            "backend": address.backend,
            "backend_name": address.backend_name,
            "geoaddress_id": address.geoaddress_id,
            "search_used": address.search_used,
        }
        result.append(address_data)
    
    if format_type == "json":
        return JsonResponse({"addresses": result, "count": len(result)}, json_dumps_params={"ensure_ascii": False})
    
    # HTML format (default)
    # Get providers list for backend filter
    providers = ProviderModel.objects.all()
    
    context = {
        "addresses": result,
        "query": query,
        "backend": backend,
        "first": first,
        "count": len(result),
        "providers": providers,
    }
    return render(request, "djgeoaddress/address_list.html", context)

