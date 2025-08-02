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
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')
    
    return value_str.endswith(image_extensions)