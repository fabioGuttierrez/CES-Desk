from django import template

register = template.Library()


@register.filter
def dictget(d, key):
    """Return d[key], or an empty list if the key doesn't exist."""
    return d.get(key, [])
