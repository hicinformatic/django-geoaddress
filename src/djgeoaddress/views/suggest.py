"""Views for address suggestions."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from ..managers.suggest import AddressManager
from ..models.provider import GeoaddressProviderModel
from ..models.suggest import AddressModel

from . import geoaddressview_enabled_and_login


@geoaddressview_enabled_and_login("GEOADDRESS_ADDRESSVIEW")
def search_addresses(request: HttpRequest) -> HttpResponse:
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
        return JsonResponse(
            {"addresses": result, "count": len(result)}, json_dumps_params={"ensure_ascii": False}
        )

    # HTML format (default)
    # Get providers list for backend filter
    providers = ProviderModel.objects.all()

    context = {
        "results": result,
        "query": query,
        "backend": backend,
        "first": first,
        "count": len(result),
        "providers": providers,
    }
    return render(request, "djgeoaddress/address_list.html", context)


@geoaddressview_enabled_and_login("GEOADDRESS_ADDRESSVIEW")
def detail_address(request: HttpRequest, geoaddress_id: str) -> HttpResponse:
    """Detail address view.

    Args:
        request: Django request object
        geoaddress_id: Combined backend_name-reference ID

    Returns:
        HTML response with address details
    """
    parts = geoaddress_id.split("-", 1)
    if len(parts) != 2:
        from django.http import Http404

        raise Http404("Invalid geoaddress ID format")
    kwargs = {
        "reference": parts[1],
        "backend": parts[0],
    }
    manager = AddressManager(**kwargs)
    manager.model = AddressModel
    qs = manager.get_queryset()
    address = qs.first()
    return render(request, "djgeoaddress/address_detail.html", {"address": address})


def redirect_to_address_list(request: HttpRequest) -> HttpResponse:
    """Redirect to address list view with query parameters.

    Args:
        request: Django request object

    Returns:
        Redirect response to address list or admin autocomplete view
    """
    query_params = request.GET.copy()
    from_url = query_params.pop("from_url", None)

    try:
        if from_url:
            url_resolver = resolve(from_url[0] if isinstance(from_url, list) else from_url)
            if url_resolver.app_name == "admin":
                base_url = reverse("admin:djgeoaddress_addressmodel_address_autocomplete_view")
                if query_params:
                    base_url += f"?{query_params.urlencode()}"
                return redirect(base_url)
    except (Resolver404, NoReverseMatch):
        pass

    base_url = reverse("djgeoaddress:search_addresses")
    if query_params:
        base_url += f"?{query_params.urlencode()}"
    return redirect(base_url)


def redirect_to_address(request: HttpRequest) -> HttpResponse:
    """Redirect to address view.

    Args:
        request: Django request object

    Returns:
        Redirect response to address detail or admin page
    """
    geoaddress_id = request.GET.get("geoaddress_id")
    if not geoaddress_id:
        return redirect(reverse("djgeoaddress:list_addresses"))
    try:
        from_url = request.GET.get("from_url")
        if from_url:
            url_resolver = resolve(from_url)
            if url_resolver.app_name == "admin":
                return redirect(
                    reverse("admin:djgeoaddress_addressmodel_change", args=[geoaddress_id])
                )
    except (Resolver404, NoReverseMatch):
        pass
    return redirect(reverse("djgeoaddress:detail_address", args=[geoaddress_id]))
