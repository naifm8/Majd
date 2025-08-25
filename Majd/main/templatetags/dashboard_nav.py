# main/templatetags/dashboard_nav.py
from django import template
from django.urls import reverse

register = template.Library()

@register.filter(name="is_active")
def is_active(request, url_value):
    """Return True if request.path equals/starts-with the target URL."""
    try:
        target = reverse(url_value)      # allow named URLs
    except Exception:
        target = str(url_value)          # or raw path

    current = (request.path or "").rstrip("/")
    target  = (target or "").rstrip("/")
    return current == target or current.startswith(target)
