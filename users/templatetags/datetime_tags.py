from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def local_datetime(dt, css_class="user-datetime"):
    if not dt:
        return ""
    iso_dt = dt.isoformat()
    return mark_safe(f'<span class="{css_class}" data-datetime="{iso_dt}"></span>')
