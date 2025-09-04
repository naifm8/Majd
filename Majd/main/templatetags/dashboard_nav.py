
from django import template
from django.urls import reverse

register = template.Library()

@register.filter(name="is_active")
def is_active(request, url_value):
    """Return True if request.path equals/starts-with the target URL."""
    try:
        target = reverse(url_value)  
    except Exception:
        target = str(url_value)         

    current = (request.path or "").rstrip("/")
    target  = (target or "").rstrip("/")
    return current == target or current.startswith(target)
