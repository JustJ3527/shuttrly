"""
Test utilities for photo similarity and embedding system.

This module contains all similarity calculation functions, embedding generation,
and debugging utilities specifically for testing the photo similarity system.
"""

from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import numpy as np
import math

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
# VECTOR UTILITIES
# ===============================

def normalize_vector(vec):
    """L2 normalization of a vector"""
    if not vec:
        return None
    
    vec = np.array(vec)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return (vec / norm).tolist()


def standardize_vector(vec):
    """Standardize a vector (center and scale)"""
    if not vec or len(vec) < 2:
        return vec
    
    vec = np.array(vec)
    mean = np.mean(vec)
    std = np.std(vec)
    
    if std == 0:
        return (vec - mean).tolist()
    
    return ((vec - mean) / std).tolist()


# ===============================
# SIMILARITY FUNCTIONS
# ===============================

def calculate_similarity(embedding1, embedding2):
    """Calculate cosine similarity between two embeddings"""
    if not embedding1 or not embedding2:
        return 0.0
    
    # Convert to numpy arrays if they're lists
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


def calculate_pearson_similarity(vec1, vec2):
    """Calculate Pearson correlation between two vectors"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    # For Pearson correlation, we need to center the vectors
    # (subtract the mean) to get proper linear correlation
    vec1_centered = vec1 - np.mean(vec1)
    vec2_centered = vec2 - np.mean(vec2)
    
    # Calculate Pearson correlation on centered vectors
    correlation_matrix = np.corrcoef(vec1_centered, vec2_centered)
    if correlation_matrix.shape == (2, 2):
        return correlation_matrix[0, 1]
    else:
        return 0.0


def _parse_shutter_speed(shutter_speed_str):
    """Parse shutter speed string to numeric value in seconds"""
    if not shutter_speed_str:
        return None
    
    try:
        # Handle fractions like "1/60", "1/125", etc.
        if '/' in str(shutter_speed_str):
            parts = str(shutter_speed_str).split('/')
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                return numerator / denominator
        
        # Handle decimal values like "0.5", "2.0", etc.
        return float(shutter_speed_str)
    except (ValueError, TypeError):
        return None


def calculate_exif_numeric_similarity(photo1, photo2, method="cosine"):
    """Calculate similarity between EXIF numeric parameters (ISO, aperture, shutter_speed)"""
    # Extract numeric values
    values1 = []
    values2 = []
    
    # ISO
    if photo1.iso and photo2.iso:
        try:
            values1.append(float(photo1.iso))
            values2.append(float(photo2.iso))
        except (ValueError, TypeError):
            pass
    
    # Aperture
    if photo1.aperture and photo2.aperture:
        try:
            values1.append(float(photo1.aperture))
            values2.append(float(photo2.aperture))
        except (ValueError, TypeError):
            pass
    
    # Shutter speed
    if photo1.shutter_speed and photo2.shutter_speed:
        try:
            ss1 = _parse_shutter_speed(photo1.shutter_speed)
            ss2 = _parse_shutter_speed(photo2.shutter_speed)
            if ss1 and ss2:
                values1.append(ss1)
                values2.append(ss2)
        except (ValueError, TypeError):
            pass
    
    if not values1 or not values2 or len(values1) != len(values2):
        return 0.0
    
    # Standardize the values
    values1_std = standardize_vector(values1)
    values2_std = standardize_vector(values2)
    
    # Calculate similarity based on method
    if method == "pearson":
        return calculate_pearson_similarity(values1_std, values2_std)
    else:  # cosine
        return calculate_similarity(values1_std, values2_std)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the haversine distance between two points on the Earth's surface (in kilometers)"""
    R = 6371  # Earth's radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def calculate_exif_similarity(photo1, photo2, gamma=(0.4, 0.3, 0.2, 0.1), method="cosine"):
    """Calculate similarity between two photos based on EXIF data with proper weighting"""
    S_loc = S_time = S_cam = S_param = 0.0
    
    # Location similarity (GPS coordinates)
    if photo1.latitude and photo1.longitude and photo2.latitude and photo2.longitude:
        distance = haversine_distance(photo1.latitude, photo1.longitude, photo2.latitude, photo2.longitude)
        S_loc = math.exp(-distance / 10.0)  # d0 = 10km
        
    # Time similarity (date/time taken)
    if photo1.date_taken and photo2.date_taken:
        delta = abs((photo1.date_taken - photo2.date_taken).total_seconds()) / 3600  # hours
        S_time = math.exp(-delta / 24.0)  # d0 = 24 hours
        
    # Camera similarity
    if photo1.camera_make and photo1.camera_model and photo2.camera_make and photo2.camera_model:
        if photo1.camera_make == photo2.camera_make and photo1.camera_model == photo2.camera_model:
            S_cam = 1.0
        elif photo1.camera_make == photo2.camera_make:
            S_cam = 0.8
        elif photo1.camera_model == photo2.camera_model:
            S_cam = 0.7
        elif photo1.camera_make.split()[0] == photo2.camera_make.split()[0]:  # Same brand
            S_cam = 0.5
        else:
            S_cam = 0.1
    
    # Numeric parameters similarity (using standardized approach)
    S_param = calculate_exif_numeric_similarity(photo1, photo2, method=method)
         
    # Weighted similarity score
    y1, y2, y3, y4 = gamma
    return y1 * S_loc + y2 * S_time + y3 * S_cam + y4 * S_param


def calculate_visual_location_similarity(photo1, photo2, alpha=0.8, beta=0.2, method="cosine"):
    """Calculate similarity between two photos using embeddings and location data only"""
    # Calculate visual similarity (embeddings)
    if method == "pearson":
        S_v = calculate_pearson_similarity(photo1.embedding, photo2.embedding)
    else:  # cosine
        S_v = calculate_similarity(photo1.embedding, photo2.embedding)
    
    # Calculate location similarity only
    S_loc = 0.0
    if photo1.latitude and photo1.longitude and photo2.latitude and photo2.longitude:
        distance = haversine_distance(photo1.latitude, photo1.longitude, photo2.latitude, photo2.longitude)
        S_loc = math.exp(-distance / 10.0)  # d0 = 10km
    
    # Adaptive weighting: if location similarity is very low, rely more on visual
    if S_loc < 0.1:
        alpha = 0.95
        beta = 0.05
    
    return alpha * S_v + beta * S_loc


def calculate_hybrid_similarity(photo1, photo2, alpha=0.7, beta=0.3, method="cosine"):
    """Calculate hybrid similarity between two photos using embeddings and EXIF data"""
    # Calculate visual similarity (embeddings)
    if method == "pearson":
        S_v = calculate_pearson_similarity(photo1.embedding, photo2.embedding)
    else:  # cosine
        S_v = calculate_similarity(photo1.embedding, photo2.embedding)
    
    # Calculate EXIF similarity
    S_e = calculate_exif_similarity(photo1, photo2, method=method)
    
    # Adaptive weighting: if EXIF similarity is very low, rely more on embeddings
    if S_e < 0.1:
        alpha = 0.9
        beta = 0.1
    
    return alpha * S_v + beta * S_e


# ===============================
# SIMILARITY CACHE FUNCTIONS
# ===============================

def get_cached_similarity(photo1, photo2, method="cosine"):
    """Get cached similarity if it exists"""
    from photos.models import PhotoSimilarity
    from django.db import models
    
    try:
        # Try both directions (photo1->photo2 and photo2->photo1)
        similarity = PhotoSimilarity.objects.filter(
            models.Q(photo1=photo1, photo2=photo2) | models.Q(photo1=photo2, photo2=photo1),
            method=method
        ).first()
        
        if similarity:
            return {
                'visual': similarity.visual_similarity,
                'exif': similarity.exif_similarity,
                'final': similarity.final_similarity
            }
    except Exception as e:
        print(f"Error getting cached similarity: {e}")
    
    return None


def cache_similarity(photo1, photo2, visual_sim, exif_sim, final_sim, method="cosine"):
    """Cache calculated similarity"""
    from photos.models import PhotoSimilarity
    from django.db import models
    
    try:
        # Ensure photo1.id < photo2.id for consistency
        if photo1.id > photo2.id:
            photo1, photo2 = photo2, photo1
        
        PhotoSimilarity.objects.update_or_create(
            photo1=photo1,
            photo2=photo2,
            method=method,
            defaults={
                'visual_similarity': visual_sim,
                'exif_similarity': exif_sim,
                'final_similarity': final_sim,
            }
        )
    except Exception as e:
        print(f"Error caching similarity: {e}")


# ===============================
# FIND SIMILAR PHOTOS FUNCTIONS
# ===============================

def find_similar_photos(photo, limit=10, threshold=0.7, method="cosine"):
    """Find photos similar to the given photo based on hybrid similarity"""
    if not photo.embedding:
        print(f"DEBUG: Photo {photo.id} has no embedding")
        return []
    
    from photos.models import Photo
    
    # Get all photos with embeddings (excluding the current photo)
    photos_with_embeddings = Photo.objects.exclude(
        id=photo.id
    ).exclude(
        embedding__isnull=True
    ).exclude(
        embedding=[]
    )
    
    print(f"DEBUG: Found {photos_with_embeddings.count()} photos with embeddings to compare")
    
    similar_photos = []
    all_similarities = []  # Store all similarities for debugging
    
    for other_photo in photos_with_embeddings:
        try:
            # Calculate detailed similarities
            if method == "pearson":
                visual_sim = calculate_pearson_similarity(photo.embedding, other_photo.embedding)
            else:  # cosine
                visual_sim = calculate_similarity(photo.embedding, other_photo.embedding)
            
            exif_sim = calculate_exif_similarity(photo, other_photo, method=method)
            final_sim = calculate_hybrid_similarity(photo, other_photo, method=method)
            
            all_similarities.append({
                'photo_id': other_photo.id,
                'visual_sim': visual_sim,
                'exif_sim': exif_sim,
                'final_sim': final_sim
            })
            
            if final_sim >= threshold:
                similar_photos.append({
                    'photo': other_photo,
                    'similarity': final_sim,
                    'visual': visual_sim,
                    'exif': exif_sim,
                    'final': final_sim
                })
        except Exception as e:
            print(f"DEBUG: Error calculating similarity for photo {other_photo.id}: {e}")
            continue
    
    # Debug: Print top similarities
    all_similarities.sort(key=lambda x: x['final_sim'], reverse=True)
    print(f"DEBUG: Top 5 similarities for photo {photo.id} (method: {method}):")
    for i, sim in enumerate(all_similarities[:5]):
        print(f"  {i+1}. Photo {sim['photo_id']}: visual={sim['visual_sim']:.3f}, exif={sim['exif_sim']:.3f}, final={sim['final_sim']:.3f}")
    
    print(f"DEBUG: Found {len(similar_photos)} photos above threshold {threshold}")
    
    # Sort by similarity (highest first) and return top results
    similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_photos[:limit]


def find_similar_photos_visual_location(photo, limit=10, threshold=0.7, method="cosine", use_faiss=True):
    """Find similar photos using visual similarity + location data only with FAISS optimization"""
    if not photo.embedding:
        print(f"DEBUG: Photo {photo.id} has no embedding")
        return []
    
    from photos.models import Photo
    
    # Try FAISS first if enabled
    if use_faiss:
        try:
            from photos.faiss_index import search_similar_photos_faiss
            
            # Search using FAISS
            faiss_results = search_similar_photos_faiss(
                photo.embedding, 
                k=limit * 2,  # Get more results to filter by location
                exclude_photo_id=photo.id
            )
            
            if faiss_results:
                print(f"DEBUG: FAISS found {len(faiss_results)} similar photos")
                
                # Get photo objects and calculate location similarity
                similar_photos = []
                all_similarities = []
                
                for photo_id, visual_sim in faiss_results:
                    try:
                        other_photo = Photo.objects.get(id=photo_id)
                        
                        # Calculate location similarity
                        location_sim = 0.0
                        if photo.latitude and photo.longitude and other_photo.latitude and other_photo.longitude:
                            distance = haversine_distance(photo.latitude, photo.longitude, other_photo.latitude, other_photo.longitude)
                            location_sim = math.exp(-distance / 10.0)  # d0 = 10km
                        
                        # Calculate final similarity (visual + location)
                        final_sim = calculate_visual_location_similarity(photo, other_photo, method=method)
                        
                        all_similarities.append({
                            'photo_id': other_photo.id,
                            'visual_sim': visual_sim,
                            'location_sim': location_sim,
                            'final_sim': final_sim
                        })
                        
                        if final_sim >= threshold:
                            similar_photos.append({
                                'photo': other_photo,
                                'similarity': final_sim,
                                'visual': visual_sim,
                                'location': location_sim,
                                'final': final_sim
                            })
                    except Photo.DoesNotExist:
                        continue
                    except Exception as e:
                        print(f"DEBUG: Error processing FAISS result for photo {photo_id}: {e}")
                        continue
                
                # Debug: Print top similarities
                all_similarities.sort(key=lambda x: x['final_sim'], reverse=True)
                print(f"DEBUG: Top 5 visual+location similarities for photo {photo.id} (FAISS, method: {method}):")
                for i, sim in enumerate(all_similarities[:5]):
                    print(f"  {i+1}. Photo {sim['photo_id']}: visual={sim['visual_sim']:.3f}, location={sim['location_sim']:.3f}, final={sim['final_sim']:.3f}")
                
                print(f"DEBUG: Found {len(similar_photos)} photos above threshold {threshold} (FAISS)")
                
                # Sort by similarity (highest first) and return top results
                similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
                return similar_photos[:limit]
                
        except Exception as e:
            print(f"DEBUG: FAISS search failed, falling back to brute force: {e}")
    
    # Fallback to brute force comparison
    print(f"DEBUG: Using brute force comparison for photo {photo.id}")
    
    # Get all photos with embeddings (excluding the current photo)
    photos_with_embeddings = Photo.objects.exclude(
        id=photo.id
    ).exclude(
        embedding__isnull=True
    ).exclude(
        embedding=[]
    )
    
    print(f"DEBUG: Found {photos_with_embeddings.count()} photos with embeddings to compare")
    
    similar_photos = []
    all_similarities = []
    
    for other_photo in photos_with_embeddings:
        try:
            # Calculate visual similarity
            if method == "pearson":
                visual_sim = calculate_pearson_similarity(photo.embedding, other_photo.embedding)
            else:  # cosine
                visual_sim = calculate_similarity(photo.embedding, other_photo.embedding)
            
            # Calculate location similarity
            location_sim = 0.0
            if photo.latitude and photo.longitude and other_photo.latitude and other_photo.longitude:
                distance = haversine_distance(photo.latitude, photo.longitude, other_photo.latitude, other_photo.longitude)
                location_sim = math.exp(-distance / 10.0)  # d0 = 10km
            
            # Calculate final similarity (visual + location)
            final_sim = calculate_visual_location_similarity(photo, other_photo, method=method)
            
            all_similarities.append({
                'photo_id': other_photo.id,
                'visual_sim': visual_sim,
                'location_sim': location_sim,
                'final_sim': final_sim
            })
            
            if final_sim >= threshold:
                similar_photos.append({
                    'photo': other_photo,
                    'similarity': final_sim,
                    'visual': visual_sim,
                    'location': location_sim,
                    'final': final_sim
                })
        except Exception as e:
            print(f"DEBUG: Error calculating similarity for photo {other_photo.id}: {e}")
            continue
    
    # Debug: Print top similarities
    all_similarities.sort(key=lambda x: x['final_sim'], reverse=True)
    print(f"DEBUG: Top 5 visual+location similarities for photo {photo.id} (brute force, method: {method}):")
    for i, sim in enumerate(all_similarities[:5]):
        print(f"  {i+1}. Photo {sim['photo_id']}: visual={sim['visual_sim']:.3f}, location={sim['location_sim']:.3f}, final={sim['final_sim']:.3f}")
    
    print(f"DEBUG: Found {len(similar_photos)} photos above threshold {threshold} (brute force)")
    
    # Sort by similarity (highest first) and return top results
    similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_photos[:limit]


def find_similar_photos_cached(photo, limit=10, threshold=0.7, method="cosine", use_cache=True):
    """Find similar photos with caching support"""
    if not photo.embedding:
        print(f"DEBUG: Photo {photo.id} has no embedding")
        return []
    
    from photos.models import Photo
    
    # Get all photos with embeddings (excluding the current photo)
    photos_with_embeddings = Photo.objects.exclude(
        id=photo.id
    ).exclude(
        embedding__isnull=True
    ).exclude(
        embedding=[]
    )
    
    print(f"DEBUG: Found {photos_with_embeddings.count()} photos with embeddings to compare")
    
    similar_photos = []
    all_similarities = []
    
    for other_photo in photos_with_embeddings:
        try:
            # Check cache first if enabled
            cached_sim = None
            if use_cache:
                cached_sim = get_cached_similarity(photo, other_photo, method)
            
            if cached_sim:
                visual_sim = cached_sim['visual']
                exif_sim = cached_sim['exif']
                final_sim = cached_sim['final']
                print(f"DEBUG: Using cached similarity for photo {other_photo.id}")
            else:
                # Calculate similarities
                if method == "pearson":
                    visual_sim = calculate_pearson_similarity(photo.embedding, other_photo.embedding)
                else:  # cosine
                    visual_sim = calculate_similarity(photo.embedding, other_photo.embedding)
                
                exif_sim = calculate_exif_similarity(photo, other_photo, method=method)
                final_sim = calculate_hybrid_similarity(photo, other_photo, method=method)
                
                # Cache the result
                if use_cache:
                    cache_similarity(photo, other_photo, visual_sim, exif_sim, final_sim, method)
            
            all_similarities.append({
                'photo_id': other_photo.id,
                'visual_sim': visual_sim,
                'exif_sim': exif_sim,
                'final_sim': final_sim
            })
            
            if final_sim >= threshold:
                similar_photos.append({
                    'photo': other_photo,
                    'similarity': final_sim,
                    'visual': visual_sim,
                    'exif': exif_sim,
                    'final': final_sim
                })
        except Exception as e:
            print(f"DEBUG: Error calculating similarity for photo {other_photo.id}: {e}")
            continue
    
    # Debug: Print top similarities
    all_similarities.sort(key=lambda x: x['final_sim'], reverse=True)
    print(f"DEBUG: Top 5 similarities for photo {photo.id} (method: {method}):")
    for i, sim in enumerate(all_similarities[:5]):
        print(f"  {i+1}. Photo {sim['photo_id']}: visual={sim['visual_sim']:.3f}, exif={sim['exif_sim']:.3f}, final={sim['final_sim']:.3f}")
    
    print(f"DEBUG: Found {len(similar_photos)} photos above threshold {threshold}")
    
    # Sort by similarity (highest first) and return top results
    similar_photos.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_photos[:limit]


# ===============================
# DEBUG FUNCTIONS
# ===============================

def debug_photo_similarity(photo):
    """Debug function to analyze photo similarity data"""
    print(f"=== DEBUG PHOTO SIMILARITY FOR PHOTO {photo.id} ===")
    print(f"Title: {photo.title}")
    print(f"Has embedding: {bool(photo.embedding)}")
    if photo.embedding:
        print(f"Embedding length: {len(photo.embedding)}")
    
    # EXIF data
    print(f"EXIF Data:")
    print(f"  - Camera: {photo.camera_make} {photo.camera_model}")
    print(f"  - Lens: {photo.lens_model}")
    print(f"  - Date taken: {photo.date_taken}")
    print(f"  - Location: {photo.latitude}, {photo.longitude}")
    print(f"  - ISO: {photo.iso}")
    print(f"  - Aperture: {photo.aperture}")
    print(f"  - Shutter speed: {photo.shutter_speed}")
    
    # Test with a few other photos
    from photos.models import Photo
    other_photos = Photo.objects.exclude(id=photo.id).exclude(embedding__isnull=True).exclude(embedding=[])[:3]
    
    for other_photo in other_photos:
        print(f"\n--- Comparing with Photo {other_photo.id} ---")
        embedding_sim = calculate_similarity(photo.embedding, other_photo.embedding)
        exif_sim = calculate_exif_similarity(photo, other_photo)
        hybrid_sim = calculate_hybrid_similarity(photo, other_photo)
        
        print(f"Embedding similarity: {embedding_sim:.3f}")
        print(f"EXIF similarity: {exif_sim:.3f}")
        print(f"Hybrid similarity: {hybrid_sim:.3f}")
    
    print("=== END DEBUG ===")
