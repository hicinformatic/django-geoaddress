"""Shared admin utilities."""

from typing import Callable, Iterable, Optional

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.html import format_html


def find_object_by_identifier(
    queryset: Iterable,
    identifier: Optional[str],
    extra_matcher: Optional[Callable[[object, str], bool]] = None,
):
    """Find an entry by matching pk/name/slug with optional custom matcher."""
    if identifier is None:
        return None
    identifier_lower = identifier.lower()

    for entry in queryset:
        name = getattr(entry, "name", "")
        if isinstance(name, str) and name.lower() == identifier_lower:
            return entry
        slug = getattr(entry, "slug", "")
        if isinstance(slug, str) and slug.lower() == identifier_lower:
            return entry
        if extra_matcher and extra_matcher(entry, identifier_lower):
            return entry
    return None


def render_settings_row(icon, key, status_html, value_html):
    """Render a standard settings table row used across admins."""
    return format_html(
        "<tr>"
        '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
        '<td style="padding: 8px; border-bottom: 1px solid #ddd;"><code>{}</code></td>'
        '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
        '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
        "</tr>",
        icon,
        key,
        status_html,
        value_html,
    )


def get_object_with_identifier(
    admin_instance,
    request,
    object_id,
    from_field=None,
    extra_matcher=None,
):
    """Shared implementation of get_object with identifier fallback."""
    if object_id is None:
        return None
    try:
        queryset = admin_instance.get_queryset(request)
        try:
            return queryset.get(pk=object_id)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return find_object_by_identifier(queryset, object_id, extra_matcher)
    except Exception:
        parent = super(type(admin_instance), admin_instance)
        return parent.get_object(request, object_id, from_field)
