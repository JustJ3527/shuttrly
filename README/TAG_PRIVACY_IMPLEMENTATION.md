# Tag Privacy Implementation

## Overview

This document describes the implementation of privacy-aware tag display functionality in the Shuttrly photo management system. The system now displays photos and collections based on user privacy settings when viewing content by tags.

## Key Features

### 1. Model Changes

The system has been updated to use `is_private` instead of `is_public` for photos and collections:

- **Photos:** `is_private = models.BooleanField(default=False)` - Photos are public by default
- **Collections:** `is_private = models.BooleanField(default=False)` - Collections are public by default
- **Users:** `is_private = models.BooleanField(default=False)` - User profiles are public by default

This change makes the privacy logic more intuitive: `is_private = False` means the content is public and visible to everyone.

### 2. Privacy-Based Content Display

The system now follows this logic for displaying tagged content:

- **If user profile is NOT private (`user.is_private = False`):**
  - Shows all non-private photos containing the specified tag from all users
  - Shows all non-private collections containing the specified tag from all users
  
- **If user profile IS private (`user.is_private = True`):**
  - Shows only the user's own photos containing the specified tag
  - Shows only the user's own collections containing the specified tag

### 2. Modified Views

#### `tag_detail` View
- **File:** `shuttrly/photos/views.py`
- **Function:** `tag_detail(request, tag_name)`
- **Changes:** Added privacy logic to filter photos and collections based on user privacy settings

#### `search_by_tags` View
- **File:** `shuttrly/photos/views.py`
- **Function:** `search_by_tags(request)`
- **Changes:** Added privacy logic to search across all public content or only user's content

#### `photo_detail` View
- **File:** `shuttrly/photos/views.py`
- **Function:** `photo_detail(request, photo_id)`
- **Changes:** Modified to allow access to public photos from other users, with privacy-based related photos

#### `collection_detail` View
- **File:** `shuttrly/photos/views.py`
- **Function:** `collection_detail(request, collection_id)`
- **Changes:** Added privacy context for consistent behavior

### 3. Utility Files and Admin Updates

#### `utils.py`
- **File:** `shuttrly/photos/utils.py`
- **Changes:** Updated all functions to use `is_private` instead of `is_public`
- **Functions Updated:**
  - `create_collection_from_photos()`: Parameter changed from `is_public` to `is_private`
  - `search_collections()`: Filter logic updated to use `is_private=False` for public content
  - `get_user_collections()`: Filter logic updated to use `is_private=False` for public content
  - `duplicate_collection()`: Default value changed to `is_private=True`

#### `tests.py`
- **File:** `shuttrly/photos/tests.py`
- **Changes:** Updated test methods to use `is_private` instead of `is_public`
- **Tests Updated:**
  - `test_photo_public_private()`: Logic inverted to test `is_private` field

#### `admin.py`
- **File:** `shuttrly/photos/admin.py`
- **Changes:** Updated admin interface to use `is_private` instead of `is_public`
- **Updates:**
  - `PhotoAdmin`: `list_display`, `list_filter`, `fieldsets`, and actions updated
  - `CollectionAdmin`: `list_display` and `list_filter` updated
  - Admin actions: `make_public()` and `make_private()` logic inverted

### 4. Template Updates

#### `tag_detail.html`
- **File:** `shuttrly/photos/templates/photos/tag_detail.html`
- **Changes:**
  - Added privacy notice showing whether content is filtered or shows all public content
  - Added user indicators for photos/collections not owned by the current user
  - Enhanced styling for privacy-related elements

### 4. Access Control

The system maintains proper access control:

- Users can only view public photos/collections from other users
- Private content remains inaccessible to non-owners
- Related photos in detail views respect privacy settings

## Implementation Details

### Privacy Check Logic

```python
# Check if user profile is private
user_is_private = getattr(request.user, 'is_private', False)

# Get photos with this tag based on privacy settings
if user_is_private:
    # If user is private, only show their own photos
    photos = Photo.objects.filter(
        user=request.user,
        tags__icontains=f"#{tag_name}"
    ).order_by('-created_at')
else:
    # If user is not private, show all non-private photos with this tag
    photos = Photo.objects.filter(
        tags__icontains=f"#{tag_name}",
        is_private=False
    ).order_by('-created_at')
```

### User Interface Indicators

- **Privacy Notice:** Shows at the top of tag pages indicating whether content is filtered
- **Owner Badges:** Display username for photos/collections not owned by the current user
- **Visual Cues:** Different styling for owned vs. other users' content

## Testing

A comprehensive test suite has been created in `test_tag_privacy.py` that verifies:

1. **Public Users:** Can see all public content with tags from all users
2. **Private Users:** Only see their own content with tags
3. **Access Control:** Proper enforcement of privacy settings
4. **Search Functionality:** Privacy-aware tag searching
5. **Detail Views:** Proper access to public content from other users

### Running Tests

```bash
# Run the specific test file
python manage.py test photos.test_tag_privacy

# Or run all tests
python manage.py test
```

## Benefits

1. **Enhanced Discovery:** Public users can discover content from other users through tags
2. **Privacy Respect:** Private users maintain their privacy preferences
3. **Better User Experience:** Clear indicators show content ownership and privacy status
4. **Scalability:** System can handle content from multiple users efficiently

## Future Enhancements

Potential improvements could include:

1. **Tag Analytics:** Show tag popularity across all public content
2. **Collaborative Tagging:** Allow users to suggest tags for public content
3. **Tag Recommendations:** Suggest related tags based on public content
4. **Privacy Granularity:** More fine-grained privacy controls for specific tags

## Security Considerations

- All access control is enforced at the view level
- Private content remains completely inaccessible to non-owners
- User privacy settings are respected throughout the system
- No information leakage about private content

## Compatibility

This implementation is backward compatible and doesn't affect existing functionality. Users with existing privacy settings will continue to work as expected, with enhanced functionality for public users.

## Migration

Deux fichiers de migration ont été créés pour mettre à jour la base de données existante :

### 1. Migration de structure (0005_rename_is_public_to_is_private.py)
Renomme les champs `is_public` en `is_private` dans les modèles Photo et Collection.

### 2. Migration de données (0006_convert_is_public_values.py)
Convertit les valeurs existantes pour maintenir la logique de confidentialité :
- `is_public=True` (ancien) → `is_private=False` (nouveau) = Public
- `is_public=False` (ancien) → `is_private=True` (nouveau) = Privé

Pour appliquer les migrations :

```bash
python manage.py migrate photos
```

**Note importante :** Cette migration inverse la logique des valeurs existantes pour maintenir le comportement attendu.

