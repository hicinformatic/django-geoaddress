"""Views for address suggestions."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS

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

    # Get addresses using the same method as admin
    addresses = []

    if query:
        kwargs = {"first": first}
        if backend:
            kwargs["attribute_search"] = {"name": backend}
        addresses = AddressModel.objects.addresses_autocomplete(query=query, **kwargs)
        
    times = AddressModel.objects.get_response_times('addresses_autocomplete')

    if format_type == "json":
        result = []
        for address in addresses:
            address_data = {field: getattr(address, field, None) for field in GEOADDRESS_FIELDS_DESCRIPTIONS}
            address_data["times"] = times.get(address.backend, 0)
            result.append(address_data)
            
        return JsonResponse(
            {"addresses": result, "count": len(result)}, json_dumps_params={"ensure_ascii": False}
        )

    # HTML format (default)
    # Get providers list for backend filter
    providers = GeoaddressProviderModel.objects.all()

    context = {
        "addresses": addresses,  # Pass the queryset directly like admin does
        "query": query,
        "backend": backend,
        "first": first,
        "count": len(addresses),
        "providers": providers,
        "times": times,

    }
    return render(request, "djgeoaddress/address_list.html", context)


@geoaddressview_enabled_and_login("GEOADDRESS_ADDRESSVIEW")
def detail_address(request: HttpRequest, geoaddress_id: str) -> HttpResponse:
    """Detail address view.

    Args:
        request: Django request object
        geoaddress_id: Combined backend_name-latitude:longitude ID (format: name_lat:lon)

    Returns:
        HTML response with address details
    """
    # Use reverse_geocode like the admin does
    qs = AddressModel.objects.reverse_geocode(geoaddress_id=geoaddress_id)
    address = qs.first()
    
    if not address:
        from django.http import Http404
        raise Http404("Address not found")
    
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
