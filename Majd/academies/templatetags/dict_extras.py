# academies/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dict lookups by key in templates."""
    if dictionary and key in dictionary:
        return dictionary.get(key)
    return None
