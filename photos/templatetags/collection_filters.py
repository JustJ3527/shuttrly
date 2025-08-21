from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def format_file_size(bytes_value):
    """Format file size in human readable format"""
    if not bytes_value:
        return "0 B"
    
    try:
        bytes_value = int(bytes_value)
    except (ValueError, TypeError):
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            if unit == 'B':
                return f"{bytes_value} {unit}"
            else:
                return f"{floatformat(bytes_value, 1)} {unit}"
        bytes_value /= 1024.0
    
    return f"{floatformat(bytes_value, 1)} TB"

@register.filter
def truncate_tags(tags, max_length=50):
    """Truncate tags string to specified length"""
    if not tags:
        return ""
    
    if len(tags) <= max_length:
        return tags
    
    # Try to truncate at word boundary
    truncated = tags[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can find a good break point
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."

@register.filter
def tag_count(photo_list, tag):
    """Count photos with a specific tag"""
    if not photo_list:
        return 0
    
    count = 0
    for photo in photo_list:
        if photo.tags and f"#{tag}" in photo.tags:
            count += 1
    
    return count

@register.filter
def collection_photo_count(collection):
    """Get photo count for a collection"""
    try:
        return collection.get_photo_count()
    except:
        return 0

@register.filter
def collection_total_size(collection):
    """Get total size for a collection"""
    try:
        return collection.get_total_size_mb()
    except:
        return 0

@register.filter
def has_tag(item, tag):
    """Check if item has a specific tag"""
    try:
        return item.has_tag(tag)
    except:
        return False

@register.filter
def get_tags_list(item):
    """Get tags list for an item"""
    try:
        return item.get_tags_list()
    except:
        return []

@register.filter
def is_owner(user, collection):
    """Check if user is owner of collection"""
    try:
        return user == collection.owner
    except:
        return False

@register.filter
def is_collaborator(user, collection):
    """Check if user is collaborator of collection"""
    try:
        return user in collection.collaborators.all()
    except:
        return False

@register.filter
def can_edit_collection(user, collection):
    """Check if user can edit collection"""
    try:
        return user == collection.owner or user in collection.collaborators.all()
    except:
        return False
