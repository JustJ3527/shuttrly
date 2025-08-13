from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import datetime

register = template.Library()


@register.simple_tag
def local_datetime(dt, css_class="user-datetime"):
    if not dt:
        return ""
    iso_dt = dt.isoformat()
    return mark_safe(f'<span class="{css_class}" data-datetime="{iso_dt}"></span>')


@register.filter
def format_date(value):
    """
    Format a date in a user-friendly way.

    Args:
        value: Date or datetime object

    Returns:
        Formatted date string
    """
    if not value:
        return ""

    if isinstance(value, datetime):
        # If it's a datetime, check if it's today
        now = timezone.now()
        if value.date() == now.date():
            return f"Today at {value.strftime('%H:%M')}"
        elif value.date() == (now.date() - timezone.timedelta(days=1)):
            return f"Yesterday at {value.strftime('%H:%M')}"
        else:
            return value.strftime("%B %d, %Y")
    else:
        # If it's just a date
        return value.strftime("%B %d, %Y")
