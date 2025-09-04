"""
Combined test views for photo similarity system.

This module contains all test views including advanced similarity testing,
legacy embedding tests, and hybrid system tests.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from photos.models import Photo
from .test_utils import (
    find_similar_photos_cached,
    find_similar_photos_visual_location,
    calculate_similarity,
    calculate_pearson_similarity,
    calculate_exif_similarity,
    debug_photo_similarity,
)


@login_required
def test_advanced_similarity_view(request, photo_id=None):
    """Vue de test avancée pour comparer toutes les méthodes de similarité"""
    
    # Get all photos with embeddings for navigation
    photos_with_embeddings = Photo.objects.exclude(
        embedding__isnull=True
    ).exclude(
        embedding=[]
    ).order_by('id')
    
    # Debug: Print available photo IDs
    print(f"DEBUG: Available photos with embeddings: {[p.id for p in photos_with_embeddings[:10]]}")
    
    if not photos_with_embeddings.exists():
        context = {
            'error': 'No photos with embeddings found. Please generate embeddings first.',
            'total_photos': Photo.objects.count(),
            'photos_with_embeddings': 0,
        }
        return render(request, 'test/test_advanced_similarity.html', context)
    
    # Get current photo - check both URL parameter and GET parameter
    photo_id_from_url = photo_id  # From URL path
    photo_id_from_get = request.GET.get('photo_id')  # From GET parameters
    
    # Use GET parameter if available, otherwise use URL parameter
    effective_photo_id = photo_id_from_get or photo_id_from_url
    
    if effective_photo_id:
        try:
            current_photo = photos_with_embeddings.get(id=effective_photo_id)
        except Photo.DoesNotExist:
            current_photo = photos_with_embeddings.first()
    else:
        current_photo = photos_with_embeddings.first()
    
    # Get navigation info
    photos_list = list(photos_with_embeddings)
    current_index = photos_list.index(current_photo)
    
    # Navigation photos
    prev_photo = photos_list[current_index - 1] if current_index > 0 else None
    next_photo = photos_list[current_index + 1] if current_index < len(photos_list) - 1 else None
    
    # Get test parameters from request
    threshold = float(request.GET.get('threshold', 0.5))
    limit = int(request.GET.get('limit', 10))
    use_cache = request.GET.get('use_cache', 'true').lower() == 'true'
    
    # Test results storage
    test_results = {}
    
    try:
        import time
        
        # Test 1: Cosine similarity
        start_time = time.time()
        cosine_results = find_similar_photos_cached(
            current_photo,
            limit=limit,
            threshold=threshold,
            method="cosine",
            use_cache=use_cache
        )
        cosine_time = time.time() - start_time
        
        test_results['cosine'] = {
            'method': 'Hybrid Cosine',
            'results': cosine_results,
            'count': len(cosine_results),
            'time': cosine_time
        }
        
        # Test 2: Pearson correlation
        start_time = time.time()
        pearson_results = find_similar_photos_cached(
            current_photo,
            limit=limit,
            threshold=threshold,
            method="pearson",
            use_cache=use_cache
        )
        pearson_time = time.time() - start_time
        
        test_results['pearson'] = {
            'method': 'Hybrid Pearson',
            'results': pearson_results,
            'count': len(pearson_results),
            'time': pearson_time
        }
        
        # Test 3: Visual only (embeddings) - Cosine
        import time
        start_time = time.time()
        
        visual_cosine_results = []
        for other_photo in photos_with_embeddings.exclude(id=current_photo.id):
            try:
                visual_sim = calculate_similarity(current_photo.embedding, other_photo.embedding)
                
                if visual_sim >= threshold:
                    visual_cosine_results.append({
                        'photo': other_photo,
                        'similarity': visual_sim,
                        'visual': visual_sim,
                        'exif': 0.0,
                        'final': visual_sim
                    })
            except Exception as e:
                continue
        
        visual_cosine_results.sort(key=lambda x: x['similarity'], reverse=True)
        visual_cosine_time = time.time() - start_time
        
        test_results['visual_cosine'] = {
            'method': 'Visual Only (Cosine)',
            'results': visual_cosine_results[:limit],
            'count': len(visual_cosine_results[:limit]),
            'time': visual_cosine_time
        }
        
        # Test 4: Visual only (embeddings) - Pearson
        start_time = time.time()
        
        visual_pearson_results = []
        for other_photo in photos_with_embeddings.exclude(id=current_photo.id):
            try:
                visual_sim = calculate_pearson_similarity(current_photo.embedding, other_photo.embedding)
                
                if visual_sim >= threshold:
                    visual_pearson_results.append({
                        'photo': other_photo,
                        'similarity': visual_sim,
                        'visual': visual_sim,
                        'exif': 0.0,
                        'final': visual_sim
                    })
            except Exception as e:
                continue
        
        visual_pearson_results.sort(key=lambda x: x['similarity'], reverse=True)
        visual_pearson_time = time.time() - start_time
        
        test_results['visual_pearson'] = {
            'method': 'Visual Only (Pearson)',
            'results': visual_pearson_results[:limit],
            'count': len(visual_pearson_results[:limit]),
            'time': visual_pearson_time
        }
        
        # Test 5: Visual + Location - Cosine (with FAISS)
        start_time = time.time()
        visual_location_results = find_similar_photos_visual_location(
            current_photo,
            limit=limit,
            threshold=threshold,
            method="cosine",
            use_faiss=True
        )
        visual_location_time = time.time() - start_time
        
        test_results['visual_location'] = {
            'method': 'Visual + Location (Cosine + FAISS)',
            'results': visual_location_results,
            'count': len(visual_location_results),
            'time': visual_location_time
        }
        
        # Test 6: Visual + Location - Cosine (without FAISS for comparison)
        start_time = time.time()
        visual_location_brute_results = find_similar_photos_visual_location(
            current_photo,
            limit=limit,
            threshold=threshold,
            method="cosine",
            use_faiss=False
        )
        visual_location_brute_time = time.time() - start_time
        
        test_results['visual_location_brute'] = {
            'method': 'Visual + Location (Cosine - Brute Force)',
            'results': visual_location_brute_results,
            'count': len(visual_location_brute_results),
            'time': visual_location_brute_time
        }
        
        # Test 6: EXIF only - Cosine
        start_time = time.time()
        
        exif_cosine_results = []
        for other_photo in photos_with_embeddings.exclude(id=current_photo.id):
            try:
                exif_sim = calculate_exif_similarity(current_photo, other_photo, method="cosine")
                
                if exif_sim >= threshold:
                    exif_cosine_results.append({
                        'photo': other_photo,
                        'similarity': exif_sim,
                        'visual': 0.0,
                        'exif': exif_sim,
                        'final': exif_sim
                    })
            except Exception as e:
                continue
        
        exif_cosine_results.sort(key=lambda x: x['similarity'], reverse=True)
        exif_cosine_time = time.time() - start_time
        
        test_results['exif_cosine'] = {
            'method': 'EXIF Only (Cosine)',
            'results': exif_cosine_results[:limit],
            'count': len(exif_cosine_results[:limit]),
            'time': exif_cosine_time
        }
        
        # Test 6: EXIF only - Pearson
        start_time = time.time()
        
        exif_pearson_results = []
        for other_photo in photos_with_embeddings.exclude(id=current_photo.id):
            try:
                exif_sim = calculate_exif_similarity(current_photo, other_photo, method="pearson")
                
                if exif_sim >= threshold:
                    exif_pearson_results.append({
                        'photo': other_photo,
                        'similarity': exif_sim,
                        'visual': 0.0,
                        'exif': exif_sim,
                        'final': exif_sim
                    })
            except Exception as e:
                continue
        
        exif_pearson_results.sort(key=lambda x: x['similarity'], reverse=True)
        exif_pearson_time = time.time() - start_time
        
        test_results['exif_pearson'] = {
            'method': 'EXIF Only (Pearson)',
            'results': exif_pearson_results[:limit],
            'count': len(exif_pearson_results[:limit]),
            'time': exif_pearson_time
        }
        
    except Exception as e:
        test_results['error'] = f"Error during similarity testing: {str(e)}"
    
    # Get cache statistics
    cache_stats = {}
    if use_cache:
        from photos.models import PhotoSimilarity
        cache_stats = {
            'total': PhotoSimilarity.objects.count(),
            'cosine': PhotoSimilarity.objects.filter(method="cosine").count(),
            'pearson': PhotoSimilarity.objects.filter(method="pearson").count(),
        }
    
    # Get FAISS statistics
    try:
        from photos.faiss_index import get_faiss_stats
        faiss_stats = get_faiss_stats()
    except Exception as e:
        faiss_stats = {'error': str(e)}
    
    context = {
        'current_photo': current_photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo,
        'current_index': current_index + 1,
        'total_photos_with_embeddings': len(photos_list),
        'test_results': test_results,
        'test_params': {
            'threshold': threshold,
            'limit': limit,
            'use_cache': use_cache,
        },
        'cache_stats': cache_stats,
        'faiss_stats': faiss_stats,
        'total_photos': Photo.objects.count(),
    }
    
    return render(request, 'test/test_advanced_similarity.html', context)


# ===============================
# LEGACY TEST VIEWS
# ===============================

@login_required
def test_embedding_system(request, photo_id=None):
    """Test view to verify embedding system is working with navigation between photos"""
    
    # Get all photos with embeddings for navigation
    photos_with_embeddings = Photo.objects.exclude(
        embedding__isnull=True
    ).exclude(
        embedding__len=0
    ).order_by('id')
    
    if not photos_with_embeddings.exists():
        context = {
            'error': 'No photos with embeddings found. Please generate embeddings first.',
            'total_photos': Photo.objects.count(),
            'photos_with_embeddings': 0,
        }
        return render(request, 'test/test_embedding.html', context)
    
    # Get current photo
    if photo_id:
        try:
            current_photo = photos_with_embeddings.get(id=photo_id)
        except Photo.DoesNotExist:
            current_photo = photos_with_embeddings.first()
    else:
        current_photo = photos_with_embeddings.first()
    
    # Get navigation info
    photos_list = list(photos_with_embeddings)
    current_index = photos_list.index(current_photo)
    
    # Navigation photos
    prev_photo = photos_list[current_index - 1] if current_index > 0 else None
    next_photo = photos_list[current_index + 1] if current_index < len(photos_list) - 1 else None
    
    # Test similarity search
    similar_results = []
    test_result = None
    
    try:
        # Test with standard model (512 dimensions) - show more photos
        from .test_utils import find_similar_photos
        similar_results = find_similar_photos(current_photo, limit=20, threshold=0.3)
        test_result = f"Found {len(similar_results)} similar photos for '{current_photo.title}'"
        
    except Exception as e:
        similar_results = [{"error": f"Error finding similar photos: {str(e)}"}]
        test_result = f"Error testing similarity: {str(e)}"
    
    context = {
        'current_photo': current_photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo,
        'current_index': current_index + 1,  # 1-based for display
        'total_photos_with_embeddings': len(photos_list),
        'test_result': test_result,
        'similar_results': similar_results,
        'total_photos': Photo.objects.count(),
        'photos_with_embeddings': photos_with_embeddings.count(),
    }
    
    return render(request, 'test/test_embedding.html', context)


@login_required
def test_hybrid_system(request, photo_id=None):
    """Test view to verify hybrid embedding + EXIF similarity system"""
    
    # Get all photos with embeddings for navigation
    photos_with_embeddings = Photo.objects.exclude(
        embedding__isnull=True
    ).exclude(
        embedding__len=0
    ).order_by('id')
    
    if not photos_with_embeddings.exists():
        context = {
            'error': 'No photos with embeddings found. Please generate embeddings first.',
            'total_photos': Photo.objects.count(),
            'photos_with_embeddings': 0,
        }
        return render(request, 'test/test_embedding.html', context)
    
    # Get current photo
    if photo_id:
        try:
            current_photo = photos_with_embeddings.get(id=photo_id)
        except Photo.DoesNotExist:
            current_photo = photos_with_embeddings.first()
    else:
        current_photo = photos_with_embeddings.first()
    
    # Get navigation info
    photos_list = list(photos_with_embeddings)
    current_index = photos_list.index(current_photo)
    
    prev_photo = photos_list[current_index - 1] if current_index > 0 else None
    next_photo = photos_list[current_index + 1] if current_index < len(photos_list) - 1 else None
    
    # Test similarity search
    similar_results = []
    test_result = None
    
    try:
        # Debug current photo data
        debug_photo_similarity(current_photo)
        
        # Utilise la version hybride avancée (embedding + EXIF)
        # Use a reasonable threshold for production
        similar_results = find_similar_photos_cached(
            current_photo, 
            limit=20, 
            threshold=0.5,  # Reasonable threshold for hybrid similarity
            method="cosine",
            use_cache=True
        )
        test_result = f"Found {len(similar_results)} similar photos for '{current_photo.title}' (threshold: 0.5, method: cosine)"
        
    except Exception as e:
        similar_results = [{"error": f"Error finding similar photos: {str(e)}"}]
        test_result = f"Error testing similarity: {str(e)}"
    
    context = {
        'current_photo': current_photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo,
        'current_index': current_index + 1,  # 1-based for display
        'total_photos_with_embeddings': len(photos_list),
        'test_result': test_result,
        'similar_results': similar_results,
        'total_photos': Photo.objects.count(),
        'photos_with_embeddings': photos_with_embeddings.count(),
    }
    
    return render(request, 'test/test_embedding.html', context)
