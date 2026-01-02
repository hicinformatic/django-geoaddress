from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden


def check_enabled(key: str) -> bool | HttpResponseForbidden:
    """Check if feature is enabled.

    Args:
        key: Settings key to check

    Returns:
        True if enabled, HttpResponseForbidden otherwise
    """
    if hasattr(settings, key) and not getattr(settings, key, False):
        return HttpResponseForbidden("This feature is not enabled.")
    return True


def check_login(request, key: str) -> bool | HttpResponseForbidden:
    """Check if user is logged in.

    Args:
        request: Django request object
        key: Settings key to check for authentication requirement

    Returns:
        True if authenticated or not required, HttpResponseForbidden otherwise
    """
    if (
        hasattr(settings, key)
        and getattr(settings, key, False)
        and not request.user.is_authenticated
    ):
        return HttpResponseForbidden("You do not have permission to access this page.")
    return True


def check_enabled_and_login(request: HttpRequest, key: str) -> bool | HttpResponseForbidden:
    """Check if feature is enabled and user is logged in.

    Args:
        request: Django request object
        key: Settings key to check

    Returns:
        True if enabled and authenticated, HttpResponseForbidden otherwise
    """
    enabled = check_enabled(key)
    if isinstance(enabled, HttpResponseForbidden):
        return enabled
    login = check_login(request, key + "_AUTH")
    if isinstance(login, HttpResponseForbidden):
        return login
    return True


def geoaddressview_enabled_and_login(key: str):
    """Decorate view to check if feature is enabled and user is logged in.

    Args:
        key: Settings key to check

    Returns:
        Decorator function
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            check_result = check_enabled_and_login(request, key)
            if isinstance(check_result, HttpResponseForbidden):
                return check_result
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
