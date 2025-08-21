# Collections and Tags Implementation

This document describes the complete implementation of collections and tags functionality for the Shuttrly photo management system.

## Overview

The collections and tags system allows users to:
- Create and manage photo collections
- Organize photos with hashtag-based tags
- Search and filter content by tags
- Collaborate on collections with other users
- Drag and drop photo reordering within collections

## Features

### Collections
- **Personal Collections**: Private collections owned by a single user
- **Shared Collections**: Collections that can be viewed by collaborators
- **Group Collections**: Collections for team collaboration
- **Photo Management**: Add, remove, and reorder photos within collections
- **Cover Photos**: Set a representative photo for the collection
- **Privacy Controls**: Make collections public or private

### Tags
- **Hashtag System**: Use # symbol for tagging (e.g., #nature #travel)
- **Auto-formatting**: Automatically adds # to tags if missing
- **Search Functionality**: Find photos and collections by multiple tags
- **Tag Statistics**: View usage counts for each tag
- **Related Tags**: Discover similar tags and content

## Technical Implementation

### Models

#### Collection Model
```python
class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(User, blank=True)
    is_public = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True)
    cover_photo = models.ForeignKey(Photo, null=True, blank=True)
    collection_type = models.CharField(choices=COLLECTION_TYPES)
    sort_order = models.CharField(choices=SORT_OPTIONS)
    custom_order = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### CollectionPhoto Model
```python
class CollectionPhoto(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
```

### Views

#### Collection Views
- `collection_list`: Display user's collections
- `collection_detail`: Show collection with photos
- `collection_create`: Create new collection
- `collection_edit`: Edit existing collection
- `collection_delete`: Delete collection
- `collection_add_photos`: Add photos to collection
- `collection_remove_photo`: Remove photo from collection
- `collection_reorder_photos`: Reorder photos via AJAX

#### Tag Views
- `tag_list`: Display all user tags with statistics
- `tag_detail`: Show content with specific tag
- `search_by_tags`: Search by multiple tags

### URLs

```python
# Collections
path("collections/", views.collection_list, name="collection_list"),
path("collections/create/", views.collection_create, name="collection_create"),
path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
path("collections/<int:collection_id>/edit/", views.collection_edit, name="collection_edit"),
path("collections/<int:collection_id>/delete/", views.collection_delete, name="collection_delete"),
path("collections/<int:collection_id>/add-photos/", views.collection_add_photos, name="collection_add_photos"),
path("collections/<int:collection_id>/remove-photo/<int:photo_id>/", views.collection_remove_photo, name="collection_remove_photo"),
path("collections/<int:collection_id>/reorder/", views.collection_reorder_photos, name="collection_reorder_photos"),

# Tags
path("tags/", views.tag_list, name="tag_list"),
path("tags/<str:tag_name>/", views.tag_detail, name="tag_detail"),
path("tags/search/", views.search_by_tags, name="search_by_tags"),
```

### Templates

#### Collection Templates
- `collection_list.html`: Grid view of all collections
- `collection_detail.html`: Collection view with photo grid and drag & drop
- `collection_form.html`: Create/edit collection form
- `collection_add_photos.html`: Photo selection interface
- `collection_confirm_delete.html`: Delete confirmation
- `collection_remove_photo.html`: Remove photo confirmation

#### Tag Templates
- `tag_list.html`: Tag overview with statistics
- `tag_detail.html`: Tag-specific content view
- `tag_search_results.html`: Multi-tag search results

### JavaScript

#### CollectionsManager Class
- Handles drag & drop photo reordering
- Manages collection actions (edit, delete, add photos)
- AJAX operations for photo ordering
- Form validation and user feedback

#### TagsManager Class
- Tag input formatting and validation
- Search form handling
- Auto-formatting of hashtags

### CSS

The `collections.css` file provides:
- Responsive grid layouts for collections and photos
- Hover effects and animations
- Mobile-friendly design
- Consistent styling across all collection and tag pages

## Usage Examples

### Creating a Collection
1. Navigate to `/photos/collections/create/`
2. Fill in collection name, description, and tags
3. Choose collection type and privacy settings
4. Add collaborators if desired
5. Save the collection

### Adding Tags to Photos
1. Edit a photo or create a new one
2. In the tags field, enter tags with # symbol
3. Tags are automatically formatted (e.g., "nature travel" becomes "#nature #travel")
4. Save the photo

### Searching by Tags
1. Go to `/photos/tags/`
2. Use the search form to enter multiple tags
3. View results in photos and collections tabs
4. Click on individual tags to see all related content

### Managing Collections
1. View collections at `/photos/collections/`
2. Click on a collection to see details
3. Use drag & drop to reorder photos
4. Add/remove photos as needed
5. Edit collection settings or delete if no longer needed

## API Endpoints

### Collection Reordering
```javascript
POST /photos/collections/{id}/reorder/
{
    "photo_order": [1, 3, 2, 4]
}
```

### Collection Management
- `GET /photos/collections/` - List collections
- `POST /photos/collections/create/` - Create collection
- `PUT /photos/collections/{id}/edit/` - Edit collection
- `DELETE /photos/collections/{id}/delete/` - Delete collection

## Security Features

- **User Authentication**: All collection operations require login
- **Ownership Verification**: Users can only modify their own collections
- **Collaborator Permissions**: Limited access for collection collaborators
- **CSRF Protection**: All forms include CSRF tokens
- **Input Validation**: Tag formatting and collection data validation

## Performance Considerations

- **Lazy Loading**: Photos load as needed in grids
- **Database Indexing**: Optimized queries for tags and collections
- **AJAX Operations**: Smooth user experience for photo reordering
- **Responsive Design**: Mobile-optimized layouts

## Future Enhancements

- **Bulk Operations**: Select multiple collections/photos for batch actions
- **Advanced Search**: Filter by date ranges, camera settings, etc.
- **Collection Templates**: Pre-defined collection structures
- **Social Features**: Like, comment, and share collections
- **Export/Import**: Backup and restore collections
- **Analytics**: Collection usage statistics and insights

## Troubleshooting

### Common Issues

1. **Tags not saving**: Ensure tags start with # symbol
2. **Photos not reordering**: Check if SortableJS is loaded
3. **Permission errors**: Verify user owns the collection
4. **AJAX failures**: Check CSRF token and network connectivity

### Debug Mode

Enable Django debug mode to see detailed error messages and SQL queries.

## Contributing

When adding new features to collections or tags:

1. Update models with proper migrations
2. Add corresponding views and URLs
3. Create/update templates
4. Include JavaScript functionality
5. Add CSS styling
6. Update this documentation
7. Test thoroughly on different devices

## Support

For issues or questions about collections and tags:
1. Check the Django admin interface for data integrity
2. Review browser console for JavaScript errors
3. Check Django logs for server-side issues
4. Verify database migrations are applied
