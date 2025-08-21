from django.db.models import Q
from .models import Collection, Photo

def create_collection_from_photos(name, owner, photos, description="", tags="", is_public=False):
    """Create a new collection from a list of photos"""
    collection = Collection.objects.create(
        name=name,
        owner=owner,
        description=description,
        tags=tags,
        is_public=is_public
    )
     # Add photos to collection
    for index, photo in enumerate(photos):
        collection.add_photo(photo, order=index)

    # Set cover photo if photos exist
    if photos.exists():
        collection.cover_photo = photos.first()
        collection.save()

    return collection

def search_collections(query, user=None, public_only=False):
    """Search for collections by name, description, or tags"""
    q_objects = Q(name__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query)

    if public_only:
        collections = Collection.objects.filter(is_public=True)
    elif user:
        collections = Collection.objects.filter(
            Q(owner=user) | Q(collaborators=user) | Q(is_public=True)
            )
    else:
        collections = Collection.objects.filter(is_public=True)

    return collections.filter(q_objects)

def get_user_collections(user, include_public=False):
    """Get all collections accessible by the user"""
    if include_public:
        return Collection.objects.filter(
            Q(owner=user) | Q(collaborators=user) | Q(is_public=True)
        ).distinct()
    else:
        return Collection.objects.filter(
            Q(owner=user) | Q(collaborators=user)
        ).distinct()

def duplicate_collection(collection, new_owner, new_name=None):
    """Duplicate a collection for a new owner"""
    if new_name is None:
        new_name = f"{collection.name} (Copy)"

    new_collection = Collection.objects.create(
        name=new_name,
        owner=new_owner,
        description=collection.description,
        tags=collection.tags,
        is_public=False, # New collections are private by default
        collection_type=collection.collection_type,
        sort_order=collection.sort_order,
        cover_photo=collection.cover_photo,
    )
    #  Copy photos (this will create new CollectionPhoto instances)
    for collection_photo in collection.collection_photos.all():
        new_collection.add_photo(
            collection_photo.photo,
            order=collection_photo.order
        )
    return new_collection

def get_collection_by_id(collection_id):
    """Get a collection by its ID"""
    try:
        return Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        return None

def get_collection_stats(collection):
    """Get statistics for a collection"""
    photos = collection.collection_photos.count()

    stats = {
        "total_photos": photos.count(),
        "total_size_mb": collection.get_total_size_mb(),
        "date_range": None,
        "camera_stats": {},
        "lens_stats": {},
        "tags_stats": {},
    }

    if photos.exists():
        # Get date range
        dates = [photo.date_taken for photo in photos if photo.date_taken]
        if dates:
            stats["date_range"] = {
                "earliest": min(dates),
                "latest": max(dates)
            }

        # Camera statistics
        camera_combinations = {}
        for photo in photos:
            if photo.camera_make and photo.camera_model:
                combo = f"{photo.camera_make} {photo.camera_model}"
                camera_combinations[combo] = camera_combinations.get(combo, 0) + 1
        
        stats["camera_stats"] = dict(sorted(
            camera_combinations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]) # Top 5 camera combinations

        # Lens statistics
        lens_combinations = {}
        for photo in photos:
            if photo.lens_model:
                lens_combinations[photo.lens_model] = lens_combinations.get(photo.lens_model, 0) + 1

        stats["lens_stats"] = dict(sorted(
            lens_combinations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]) # Top 5 lens combinations

        # Tag statistics
        all_tags = []
        for photo in photos:
            if photo.tags:
                # Extract hashtags from photo tags
                photo_tags = [tag.strip() for tag in photo.tags.split() if tag.strip().startswith('#')]
                # Remove # symbol for counting
                clean_tags = [tag[1:] for tag in photo_tags]
                all_tags.extend(clean_tags)
            
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        stats["tags_stats"] = dict(sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]) # Top 10 tags

    return stats
                