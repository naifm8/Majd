# academies/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dict lookups by key in templates."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return a list."""
    if value:
        return [item.strip() for item in str(value).split(delimiter) if item.strip()]
    return []