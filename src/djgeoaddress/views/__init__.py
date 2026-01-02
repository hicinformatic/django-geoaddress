from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden


def check_enabled(key: str):
    """Check if feature is enabled."""
    if hasattr(settings, key) and not getattr(settings, key, False):
        return HttpResponseForbidden("Cette fonctionnalité n'est pas activée.")
    return True


def check_login(request, key: str):
    """Check if user is logged in."""
    if hasattr(settings, key) and getattr(settings, key, False) and not request.user.is_authenticated:
        return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
    return True


def check_enabled_and_login(request, key: str):
    """Check if feature is enabled and user is logged in."""
    enabled = check_enabled(key)
    if isinstance(enabled, HttpResponseForbidden):
        return enabled
    login = check_login(request, key + '_AUTH')
    if isinstance(login, HttpResponseForbidden):
        return login
    return True


def geoaddressview_enabled_and_login(key: str):
    """Decorate view to check if feature is enabled and user is logged in."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            check_result = check_enabled_and_login(request, key)
            if isinstance(check_result, HttpResponseForbidden):
                return check_result
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator