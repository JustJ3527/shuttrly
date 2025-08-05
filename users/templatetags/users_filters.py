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
