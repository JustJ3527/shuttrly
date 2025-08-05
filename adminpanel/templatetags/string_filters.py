# adminpanel/templatetags/string_filters.py
from django import template

register = template.Library()


@register.filter
def is_image_url(value):
    """Check if the value is an image file URL"""
    if not value:
        return False

    # Convert to string and get lowercase version
    value_str = str(value).lower()

    # Check if it ends with common image extensions
    image_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")

    return value_str.endswith(image_extensions)


from django import template

register = template.Library()


@register.filter
def format_location(location):
    if not location or not isinstance(location, dict):
        return "Localisation inconnue"

    city = location.get("city")
    region = location.get("region")
    country = location.get("country")

    parts = [part for part in [city, region, country] if part]
    return ", ".join(parts) if parts else "Localisation inconnue"
