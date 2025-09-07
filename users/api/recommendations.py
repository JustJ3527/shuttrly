# users/api/recommendations.py - API endpoints for user recommendations
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from users.utilsFolder.recommendations import get_recommendations_for_display, get_user_recommendations_cached
from users.tasks import calculate_user_recommendations_task, update_recommendation_cache
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_recommendations(request):
    """
    Get user recommendations for the authenticated user.
    
    Query parameters:
    - limit: Number of recommendations to return (default: 5)
    - force_refresh: Force recalculation (default: false)
    """
    try:
        user = request.user
        limit = int(request.GET.get('limit', 5))
        force_refresh = request.GET.get('force_refresh', 'false').lower() == 'true'
        
        # Limit the number of recommendations
        limit = min(limit, 20)  # Max 20 recommendations
        
        if force_refresh:
            # Force recalculation
            calculate_user_recommendations_task.delay(user.id, force_recalculate=True)
            return Response({
                'status': 'success',
                'message': 'Recommendation calculation started in background',
                'recommendations': []
            })
        
        # Get recommendations
        recommendations = get_recommendations_for_display(user.id, limit=limit)
        
        return Response({
            'status': 'success',
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as exc:
        logger.error(f"Error getting user recommendations: {exc}")
        return Response({
            'status': 'error',
            'message': 'Failed to get recommendations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_recommendation_calculation(request):
    """
    Trigger recommendation calculation for the authenticated user.
    This is useful when you want to ensure fresh recommendations.
    """
    try:
        user = request.user
        
        # Try Celery first, fallback to direct calculation
        try:
            task = calculate_user_recommendations_task.delay(user.id, force_recalculate=True)
            return Response({
                'status': 'success',
                'message': 'Recommendation calculation started in background',
                'task_id': task.id
            })
        except Exception as celery_error:
            logger.warning(f"Celery not available, using direct calculation: {celery_error}")
            
            # Fallback: direct calculation for specific user
            from users.utilsFolder.recommendations import build_user_recommendations_for_user
            try:
                # Recalculate recommendations for this specific user only
                result = build_user_recommendations_for_user(user.id)
                
                if result.get('success'):
                    return Response({
                        'status': 'success',
                        'message': f'Recommendations recalculated successfully for {result.get("username", user.username)}',
                        'recommendations_count': result.get('recommendations_count', 0)
                    })
                else:
                    return Response({
                        'status': 'error',
                        'message': f'Failed to recalculate recommendations: {result.get("error", "Unknown error")}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as calc_error:
                logger.error(f"Error in direct calculation: {calc_error}")
                return Response({
                    'status': 'error',
                    'message': f'Failed to recalculate recommendations: {str(calc_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as exc:
        logger.error(f"Error triggering recommendation calculation: {exc}")
        return Response({
            'status': 'error',
            'message': f'Failed to start recommendation calculation: {str(exc)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendation_stats(request):
    """
    Get statistics about user recommendations.
    """
    try:
        user = request.user
        
        # Get recommendations from cache/database
        recommendations = get_user_recommendations_cached(user.id, top_k=50)
        
        stats = {
            'total_recommendations': len(recommendations),
            'has_recommendations': len(recommendations) > 0,
            'average_score': sum(r['score'] for r in recommendations) / len(recommendations) if recommendations else 0,
            'top_score': max(r['score'] for r in recommendations) if recommendations else 0,
            'public_users': len([r for r in recommendations if not r.get('is_private', False)]),
            'private_users': len([r for r in recommendations if r.get('is_private', False)])
        }
        
        return Response({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as exc:
        logger.error(f"Error getting recommendation stats: {exc}")
        return Response({
            'status': 'error',
            'message': 'Failed to get recommendation statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_all_recommendations(request):
    """
    Trigger refresh of all user recommendations (admin function).
    This should be called periodically to keep recommendations fresh.
    """
    try:
        # Check if user is staff (admin only)
        if not request.user.is_staff:
            return Response({
                'status': 'error',
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Trigger background calculation for all users
        task = calculate_user_recommendations_task.delay()
        
        return Response({
            'status': 'success',
            'message': 'Full recommendation calculation started',
            'task_id': task.id
        })
        
    except Exception as exc:
        logger.error(f"Error refreshing all recommendations: {exc}")
        return Response({
            'status': 'error',
            'message': 'Failed to start full recommendation calculation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
