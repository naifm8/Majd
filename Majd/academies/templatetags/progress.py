# academies/templatetags/progress.py
from django import template
register = template.Library()

@register.filter
def percent(value, total):
    try:
        return round((value / total) * 100, 1) if total else 0
    except:
        return 0

# academies/templatetags/progress.py
from django import template

register = template.Library()

@register.filter
def percent(value, total):
    """
    Calculate percentage (value / total * 100).
    Returns integer percent (0–100).
    """
    try:
        return round((value / total) * 100, 1) if total else 0
    except Exception:
        return 0
