import re
from django import template

register = template.Library()

@register.filter
def underscore_to_space(value):
    if isinstance(value, str):
        return value.replace('_', ' ')
    return value

@register.filter
def camel_to_space(value):
    if isinstance(value, str):
        s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', value)
        return s1.replace('_', ' ')
    return value

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def add_http(url):
    if isinstance(url, str):
        if url.startswith(('http://', 'https://')):
            return url
        return 'http://' + url
    return url

@register.filter
def visible_items(obj):
    """
    From a dict, return a list of (key, val) pairs
    excluding any "show*" flags or control-only fields.
    """
    if isinstance(obj, dict):
        return [
            (k, v) for k, v in obj.items()
            if not k.startswith('show')
               and k not in ('sliderStyle','level','alignment')
               and v not in (None, '')
        ]
    return []
