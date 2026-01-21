"""View for geoaddress home page."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from . import geoaddressview_enabled_and_login


@geoaddressview_enabled_and_login("GEOADDRESS_PROVIDERVIEW")
def index(request: HttpRequest) -> HttpResponse:
    """Home page for geoaddress with links to providers and suggest.

    Args:
        request: Django request object

    Returns:
        HTML response with navigation links
    """
    context = {
        "providers_url": reverse("djgeoaddress:list_providers"),
        "suggest_url": reverse("djgeoaddress:search_addresses"),
    }
    return render(request, "djgeoaddress/index.html", context)
