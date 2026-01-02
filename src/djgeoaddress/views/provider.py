"""Views for provider listing."""

from django.http import JsonResponse
from django.shortcuts import render
from ..models.provider import ProviderModel
from . import geoaddressview_enabled_and_login


@geoaddressview_enabled_and_login("GEOADDRESS_PROVIDERVIEW")
def list_providers(request):
    """List all providers with their status and available services.
    
    Returns:
        HTML or JSON response with provider list containing:
        - name: Provider name
        - display_name: Provider display name
        - status: "available" or "not available"
        - services: List of available services (only if status is "available")
    """
    format_type = request.GET.get("format", "html")
    
    providers = ProviderModel.objects.all()
    
    result = []
    for provider in providers:
        # Check if provider is available (packages installed and config ready)
        is_available = (
            provider.are_packages_installed and 
            provider.is_config_ready
        )
        
        provider_data = {
            "name": provider.name,
            "display_name": provider.display_name,
            "status": "available" if is_available else "not available",
        }
        
        # Only include services if provider is available
        if is_available:
            provider_data["services"] = provider.services or []
        else:
            provider_data["services"] = []
        
        result.append(provider_data)
    
    if format_type == "json":
        return JsonResponse({"providers": result}, json_dumps_params={"ensure_ascii": False})
    
    # HTML format (default)
    return render(request, "djgeoaddress/provider_list.html", {"providers": result})


@geoaddressview_enabled_and_login("GEOADDRESS_PROVIDERVIEW")
def detail_provider(request, provider_name):
    """Detail provider view."""
    provider = ProviderModel.objects.get(name=provider_name)
    return render(request, "djgeoaddress/provider_detail.html", {"provider": provider})
