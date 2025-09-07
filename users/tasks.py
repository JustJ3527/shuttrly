# users/tasks.py - Celery tasks for user recommendations
from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from users.utilsFolder.recommendations import build_user_recommendations, get_user_recommendations_cached
from .models import UserRecommendation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def calculate_user_recommendations_task(self, user_id=None, force_recalculate=False):
    """
    Calculate user recommendations in background.
    
    Args:
        user_id: Specific user ID to calculate for (None for all users)
        force_recalculate: Force recalculation even if cache exists
    """
    try:
        logger.info(f"Starting recommendation calculation for user {user_id or 'all users'}")
        
        if user_id:
            # Calculate for specific user only
            user = User.objects.get(id=user_id)
            recommendations = _calculate_single_user_recommendations(user)
            
            # Cache the results
            cache_key = f"user_recommendations_{user_id}"
            cache.set(cache_key, recommendations, timeout=86400)  # 24 hours
            
            logger.info(f"Calculated {len(recommendations)} recommendations for user {user_id}")
        else:
            # Calculate for all users (batch mode)
            build_user_recommendations()
            
            # Clear all recommendation caches
            cache.delete_many([f"user_recommendations_{user.id}" for user in User.objects.all()])
            
            logger.info("Calculated recommendations for all users")
            
        return {
            'status': 'success',
            'user_id': user_id,
            'message': f'Recommendations calculated successfully'
        }
        
    except Exception as exc:
        logger.error(f"Error calculating recommendations: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying in {retry_delay} seconds...")
            raise self.retry(countdown=retry_delay, exc=exc)
        
        return {
            'status': 'error',
            'user_id': user_id,
            'message': f'Failed to calculate recommendations: {str(exc)}'
        }

@shared_task
def cleanup_old_recommendations():
    """Clean up old recommendation entries to prevent database bloat"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete recommendations older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = UserRecommendation.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old recommendations")
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as exc:
        logger.error(f"Error cleaning up old recommendations: {exc}")
        return {'status': 'error', 'message': str(exc)}

@shared_task
def update_recommendation_cache():
    """Update recommendation cache for active users"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Get users active in the last 7 days
        active_cutoff = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            last_login_date__gte=active_cutoff
        ).values_list('id', flat=True)
        
        # Update cache for active users
        for user_id in active_users:
            recommendations = get_user_recommendations_cached(user_id)
            if recommendations:
                cache_key = f"user_recommendations_{user_id}"
                cache.set(cache_key, recommendations, timeout=86400)
        
        logger.info(f"Updated recommendation cache for {len(active_users)} active users")
        return {'status': 'success', 'updated_users': len(active_users)}
        
    except Exception as exc:
        logger.error(f"Error updating recommendation cache: {exc}")
        return {'status': 'error', 'message': str(exc)}

def _calculate_single_user_recommendations(user, top_k=10):
    """
    Calculate recommendations for a single user using collaborative filtering.
    This is a simplified version for individual user calculation.
    """
    try:
        from .models import UserRelationship
        import numpy as np
        from scipy.sparse import csr_matrix
        from sklearn.preprocessing import normalize
        
        # Get all users except the current one
        all_users = User.objects.exclude(id=user.id).order_by('-date_joined')
        user_index = {u.id: idx for idx, u in enumerate(all_users)}
        index_user = {idx: u.id for idx, u in enumerate(all_users)}
        
        if not user_index:
            return []
        
        # Get user's following relationships
        user_following = set(UserRelationship.objects.filter(
            from_user=user,
            relationship_type="follow"
        ).values_list('to_user_id', flat=True))
        
        # Create similarity matrix based on mutual follows
        n_users = len(all_users)
        rows, cols = [], []
        
        for rel in UserRelationship.objects.filter(relationship_type="follow"):
            if rel.from_user_id in user_index and rel.to_user_id in user_index:
                rows.append(user_index[rel.from_user_id])
                cols.append(user_index[rel.to_user_id])
        
        if not rows:
            return []
        
        mat = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_users, n_users))
        mat_norm = normalize(mat, axis=0)
        item_similarity = mat_norm.T @ mat_norm
        
        # Calculate scores for the user
        user_following_indices = [user_index[uid] for uid in user_following if uid in user_index]
        
        if not user_following_indices:
            # If user follows no one, recommend popular users
            scores = np.array([1.0] * n_users)
        else:
            scores = item_similarity[user_following_indices].sum(axis=0).A1
        
        # Remove users already followed
        for idx in user_following_indices:
            scores[idx] = 0
        
        # Get top recommendations
        top_indices = np.argsort(-scores)[:top_k]
        
        recommendations = []
        for idx in top_indices:
            if scores[idx] > 0:
                recommended_user = User.objects.get(id=index_user[idx])
                recommendations.append({
                    'id': recommended_user.id,
                    'username': recommended_user.username,
                    'first_name': recommended_user.first_name,
                    'last_name': recommended_user.last_name,
                    'profile_picture_url': recommended_user.profile_picture.url if recommended_user.profile_picture else None,
                    'is_private': recommended_user.is_private,
                    'photos_count': recommended_user.get_photos_count(),
                    'score': float(scores[idx])
                })
        
        return recommendations
        
    except Exception as exc:
        logger.error(f"Error calculating single user recommendations: {exc}")
        return []


@shared_task
def build_enhanced_recommendations_task():
    """
    Celery task to build user recommendations with enhanced boosts including photo similarity.
    
    This task uses the new build_user_recommendations_with_boosts function that includes:
    - Photo similarity boost
    - New account boost
    - Activity boost
    - Recent activity boost
    """
    try:
        from .utilsFolder.recommendations import build_user_recommendations_with_boosts, User
        
        print("🚀 Starting enhanced recommendations build with photo similarity...")
        
        # Build recommendations with enhanced boosts
        recommendations = build_user_recommendations_with_boosts(
            top_k=10,
            friend_boost=1.2,
            following_boost=1.1,
            public_boost=0.8,
            follower_boost=0.5,
            photo_similarity_boost=1.1,
            new_account_boost=0.7
        )
        
        print(f"✅ Enhanced recommendations build completed. Generated {len(recommendations)} recommendations")
        
        return {
            'status': 'success',
            'message': f'Enhanced recommendations built successfully',
            'recommendations_count': len(recommendations)
        }
        
    except Exception as exc:
        print(f"❌ Error building enhanced recommendations: {exc}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error', 
            'message': str(exc),
            'recommendations_count': 0
        }


@shared_task
def build_enhanced_recommendations_for_user_task(user_id):
    """
    Celery task to build enhanced recommendations for a specific user.
    
    Args:
        user_id: ID of the user to build recommendations for
    """
    try:
        from .utilsFolder.recommendations import get_user_recommendations_with_enhanced_boosts
        
        print(f"🚀 Building enhanced recommendations for user {user_id}...")
        
        # Get recommendations with enhanced boosts
        recommendations = get_user_recommendations_with_enhanced_boosts(user_id, top_k=10)
        
        print(f"✅ Enhanced recommendations for user {user_id} completed. Generated {len(recommendations)} recommendations")
        
        return {
            'status': 'success',
            'message': f'Enhanced recommendations built for user {user_id}',
            'user_id': user_id,
            'recommendations_count': len(recommendations),
            'recommendations': recommendations[:5]  # Return top 5 for logging
        }
        
    except Exception as exc:
        print(f"❌ Error building enhanced recommendations for user {user_id}: {exc}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error', 
            'message': str(exc),
            'user_id': user_id,
            'recommendations_count': 0
        }