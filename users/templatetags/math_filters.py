from django import template
from datetime import date

register = template.Library()


@register.filter(name="mul")
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter(name="calculate_age")
def calculate_age(birth_date):
    """Calculate age from date of birth"""
    try:
        today = date.today()
        age = today.year - birth_date.year
        # Check if birthday has occurred this year
        if today.month < birth_date.month or (
            today.month == birth_date.month and today.day < birth_date.day
        ):
            age -= 1
        return age
    except (ValueError, TypeError, AttributeError):
        return None
