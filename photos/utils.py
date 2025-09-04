from django.db.models import Q
from .models import Collection, Photo
import math

def create_collection_from_photos(name, owner, photos, description="", tags="", is_private=False):
    """Create a new collection from a list of photos"""
    collection = Collection.objects.create(
        name=name,
        owner=owner,
        description=description,
        tags=tags,
        is_private=is_private
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
        collections = Collection.objects.filter(is_private=False)
    elif user:
        collections = Collection.objects.filter(
            Q(owner=user) | Q(collaborators=user) | Q(is_private=False)
            )
    else:
        collections = Collection.objects.filter(is_private=False)

    return collections.filter(q_objects)

def get_user_collections(user, include_public=False):
    """Get all collections accessible by the user"""
    if include_public:
        return Collection.objects.filter(
            Q(owner=user) | Q(collaborators=user) | Q(is_private=False)
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
        is_private=True, # New collections are private by default
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

# ===============================
# EMBEDDINGS & SIMILARITY (PRODUCTION)
# ===============================
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch

# Load model once only (avoid reloading at each call)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def get_image_embedding(image_path: str):
    """Generate an embedding for a photo"""
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            embeddings = model.get_image_features(**inputs)
        # Normalize embeddings and convert to list
        embeddings = embeddings / embeddings.norm(p=2)
        return embeddings[0].tolist()
    except Exception as e:
        print(f"Error generating embedding for {image_path}: {e}")
        return None

# ===============================
# PHOTO VISIBILITY UTILITIES
# ===============================

def get_visible_photos_queryset(user, include_own_photos=True):
    """
    Get a queryset of photos that the user can see based on privacy settings.
    
    Args:
        user: The user requesting photos (can be None for anonymous users)
        include_own_photos: Whether to include the user's own photos (default: True)
    
    Returns:
        QuerySet of photos visible to the user
    """
    if not user or not user.is_authenticated:
        # Anonymous users can only see public photos from public accounts
        return Photo.objects.filter(
            is_private=False,
            user__is_private=False
        )
    
    # Build query for authenticated users
    query = Q()
    
    # Always include public photos from public accounts (excluding own photos if requested)
    if include_own_photos:
        query |= Q(is_private=False, user__is_private=False)
    else:
        # Exclude user's own photos from public photos
        query |= Q(is_private=False, user__is_private=False) & ~Q(user=user)
    
    if include_own_photos:
        # Include user's own photos (both private and public)
        query |= Q(user=user)
    
    # Include public photos from private accounts (if user can see the profile)
    # This requires checking follow relationships
    from users.models import FollowRequest
    following_users = FollowRequest.objects.filter(
        from_user=user,
        status='accepted'
    ).values_list('to_user', flat=True)
    
    if following_users:
        if include_own_photos:
            query |= Q(
                is_private=False,
                user__in=following_users
            )
        else:
            # Exclude user's own photos from followed users' photos
            query |= Q(
                is_private=False,
                user__in=following_users
            ) & ~Q(user=user)
    
    return Photo.objects.filter(query).distinct()

def can_user_see_photo(user, photo):
    """
    Check if a user can see a specific photo.
    
    Args:
        user: The user requesting to see the photo (can be None for anonymous users)
        photo: The photo to check visibility for
    
    Returns:
        bool: True if user can see the photo, False otherwise
    """
    if not photo:
        return False
    
    # Photo owner can always see their own photos
    if user and user.is_authenticated and photo.user == user:
        return True
    
    # Public photos from public accounts are visible to everyone
    if not photo.is_private and not photo.user.is_private:
        return True
    
    # Private photos are only visible to the owner
    if photo.is_private:
        return False
    
    # For public photos from private accounts, check if user can see the profile
    if user and user.is_authenticated:
        return photo.user.can_see_profile(user)
    
    return False

# ===============================
# SIMILARITY CALCULATION UTILITIES
# ===============================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in kilometers"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def calculate_cosine_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings"""
    if not embedding1 or not embedding2:
        return 0.0
    
    try:
        # Convert to numpy arrays if they're lists
        import numpy as np
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0

def calculate_visual_location_similarity(photo1, photo2, alpha=0.8, beta=0.2):
    """
    Calculate similarity between two photos using embeddings and location data.
    
    Args:
        photo1: First photo object
        photo2: Second photo object
        alpha: Weight for visual similarity (default: 0.8)
        beta: Weight for location similarity (default: 0.2)
    
    Returns:
        float: Combined similarity score between 0 and 1
    """
    # Calculate visual similarity (embeddings)
    visual_sim = 0.0
    if photo1.embedding and photo2.embedding:
        visual_sim = calculate_cosine_similarity(photo1.embedding, photo2.embedding)
    
    # Calculate location similarity
    location_sim = 0.0
    if (photo1.latitude and photo1.longitude and 
        photo2.latitude and photo2.longitude):
        distance = haversine_distance(
            photo1.latitude, photo1.longitude, 
            photo2.latitude, photo2.longitude
        )
        location_sim = math.exp(-distance / 10.0)  # d0 = 10km
    
    # Adaptive weighting: if location similarity is very low, rely more on visual
    if location_sim < 0.1:
        alpha = 0.95
        beta = 0.05
    
    return alpha * visual_sim + beta * location_sim

def find_similar_photos_with_visibility(photo, user, limit=10, threshold=0.7, include_own_photos=True):
    """
    Find photos similar to the given photo using cosine similarity + location,
    respecting privacy settings and user visibility.
    
    Args:
        photo: The photo to find similar photos for
        user: The user requesting similar photos (can be None for anonymous users)
        limit: Maximum number of similar photos to return (default: 10)
        threshold: Minimum similarity score to include (default: 0.7)
        include_own_photos: Whether to include the user's own photos (default: True)
    
    Returns:
        list: List of similar photo objects
    """
    if not photo.embedding:
        print(f"DEBUG: Photo {photo.id} has no embedding")
        return []
    
    # Get visible photos for the user
    visible_photos = get_visible_photos_queryset(user, include_own_photos)
    
    # Filter to photos with embeddings (excluding the current photo)
    photos_with_embeddings = visible_photos.exclude(
        id=photo.id
    ).exclude(
        embedding__isnull=True
    ).exclude(
        embedding=[]
    )
    
    print(f"DEBUG: Found {photos_with_embeddings.count()} visible photos with embeddings to compare")
    
    similar_photos = []
    
    for other_photo in photos_with_embeddings:
        try:
            # Calculate visual + location similarity
            similarity = calculate_visual_location_similarity(photo, other_photo)
            
            if similarity >= threshold:
                similar_photos.append({
                    'photo': other_photo,
                    'similarity': similarity
                })
        except Exception as e:
            print(f"DEBUG: Error calculating similarity for photo {other_photo.id}: {e}")
            continue
    
    # Sort by similarity (highest first) and return top results
    similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
    return [item['photo'] for item in similar_photos[:limit]]