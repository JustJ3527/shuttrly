# adminpanel/templatetags/datetime_filters.py
from django import template
from dateutil import parser  # pip install python-dateutil

register = template.Library()

@register.filter
def format_iso_datetime(value):
    """
    Parse ISO 8601 datetime string and format it nicely.
    If parsing fails, return original value.
    """
    if not value:
        return ""
    try:
        dt = parser.isoparse(value)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return value