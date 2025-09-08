# users/tasks.py - Celery tasks for user recommendations
from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.utilsFolder.recommendations import build_user_recommendations_for_user, get_user_recommendations_cached, build_user_recommendations
from .models import UserRecommendation
import logging
import random
from datetime import timedelta

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


@shared_task(bind=True)
def periodic_recommendations_update(self):
    """
    Periodic task to update recommendations for all users every 30 minutes.
    This runs in background to keep recommendations fresh.
    """
    try:
        logger.info("Starting periodic recommendations update")
        
        # Get all active users
        users = User.objects.filter(is_active=True, is_anonymized=False)
        
        # Update recommendations for each user (top 30)
        for user in users:
            try:
                result = build_user_recommendations_for_user(user.id, top_k=30)
                if result.get('success'):
                    logger.info(f"Updated top 30 recommendations for user {user.username}")
                else:
                    logger.warning(f"Failed to update recommendations for user {user.username}")
            except Exception as e:
                logger.error(f"Error updating recommendations for user {user.username}: {e}")
                continue
        
        logger.info("Periodic recommendations update completed")
        return "Periodic recommendations update completed"
        
    except Exception as exc:
        logger.error(f"Error in periodic recommendations update: {exc}")
        return f"Error in periodic recommendations update: {exc}"


def get_user_recommendations_for_display(user_id, limit=4, rotation_key=None):
    """
    Get recommendations for display with intelligent rotation.
    
    Args:
        user_id: ID of the user
        limit: Number of recommendations to return (default: 4)
        rotation_key: Key for rotation (timestamp, random, etc.)
    
    Returns:
        dict: Recommendations formatted for display
    """
    try:
        from django.contrib.auth import get_user_model
        from users.models import FollowRequest
        
        User = get_user_model()
        
        # Get current user's following list and follow requests to filter out
        try:
            user = User.objects.get(id=user_id)
            user_following = set(user.get_following().values_list('id', flat=True))
            
            # Get users to whom the current user has sent follow requests
            user_follow_requests = set(FollowRequest.objects.filter(
                from_user=user,
                status='pending'
            ).values_list('to_user_id', flat=True))
            
            print(f"🔍 DEBUG: User {user.username} follows {len(user_following)} users: {list(user_following)}")
            print(f"🔍 DEBUG: User {user.username} has pending follow requests to {len(user_follow_requests)} users: {list(user_follow_requests)}")
        except User.DoesNotExist:
            print(f"❌ User with ID {user_id} not found")
            return {
                'status': 'error',
                'message': 'User not found',
                'recommendations': []
            }
        
        # Get top 30 recommendations from database
        recommendations = UserRecommendation.objects.filter(
            user_id=user_id
        ).select_related('recommended_user').order_by('position')[:30]
        
        if not recommendations.exists():
            # No recommendations in database, trigger calculation
            calculate_user_recommendations_task.delay(user_id)
            return {
                'status': 'pending',
                'message': 'No recommendations available, calculation started',
                'recommendations': []
            }
        
        # Convert to list format and filter out users already followed and with pending requests
        recommendations_list = []
        for rec in recommendations:
            recommended_user = rec.recommended_user
            
            # Skip if already following
            if recommended_user.id in user_following:
                print(f"🔍 DEBUG: Skipping {recommended_user.username} (already following)")
                continue
                
            # Skip if follow request already sent
            if recommended_user.id in user_follow_requests:
                print(f"🔍 DEBUG: Skipping {recommended_user.username} (follow request already sent)")
                continue
            
            # Check if recommended user is still active
            if not recommended_user.is_active or recommended_user.is_anonymized:
                continue
            
            recommendations_list.append({
                'id': recommended_user.id,
                'username': recommended_user.username,
                'first_name': recommended_user.first_name,
                'last_name': recommended_user.last_name,
                'profile_picture_url': recommended_user.profile_picture.url if recommended_user.profile_picture else None,
                'is_private': recommended_user.is_private,
                'photos_count': recommended_user.get_photos_count(),
                'score': rec.score,
                'position': rec.position,
                'last_shown': rec.last_shown,
                'show_count': rec.show_count
            })
        
        # Apply intelligent rotation
        selected_recommendations = apply_intelligent_rotation(
            recommendations_list, 
            limit, 
            rotation_key
        )
        
        # Update show tracking for selected recommendations
        update_recommendation_show_tracking(selected_recommendations, user_id)
        
        print(f"🔍 DEBUG: Returning {len(selected_recommendations)} recommendations for display")
        return {
            'status': 'success',
            'recommendations': selected_recommendations,
            'count': len(selected_recommendations)
        }
        
    except Exception as exc:
        logger.error(f"Error getting recommendations for display: {exc}")
        return {
            'status': 'error',
            'message': str(exc),
            'recommendations': []
        }


def apply_intelligent_rotation(recommendations, limit=4, rotation_key=None):
    """
    Apply intelligent rotation to select recommendations.
    This function is deterministic - same rotation_key will always return same results.
    
    Args:
        recommendations: List of available recommendations
        limit: Number of recommendations to return
        rotation_key: Key for rotation (timestamp, random, etc.)
    
    Returns:
        list: Selected recommendations for display
    """
    if not recommendations:
        return []
    
    # If we have fewer recommendations than the limit, return all
    if len(recommendations) <= limit:
        return format_recommendations_for_display(recommendations)
    
    # Sort by priority (score + recency + show frequency)
    def priority_score(rec):
        base_score = rec.get('score', 0)
        
        # Reduce priority for recently shown recommendations
        last_shown = rec.get('last_shown')
        if last_shown:
            hours_since_shown = (timezone.now() - last_shown).total_seconds() / 3600
            recency_penalty = min(0.5, hours_since_shown / 24)  # Max 0.5 penalty
        else:
            recency_penalty = 0
        
        # Reduce priority for frequently shown recommendations
        show_count = rec.get('show_count', 0)
        frequency_penalty = min(0.3, show_count * 0.1)  # Max 0.3 penalty
        
        return base_score - recency_penalty - frequency_penalty
    
    # Sort by priority
    sorted_recs = sorted(recommendations, key=priority_score, reverse=True)
    
    # Use deterministic selection based on rotation_key
    if rotation_key:
        random.seed(rotation_key)
    
    # Select from top candidates with deterministic rotation
    top_candidates = sorted_recs[:min(len(sorted_recs), limit * 3)]  # Top 3x limit
    
    # Use deterministic selection instead of random.sample
    selected = []
    for i in range(min(limit, len(top_candidates))):
        # Use rotation_key + index to create deterministic selection
        if rotation_key:
            selection_index = (rotation_key + i) % len(top_candidates)
        else:
            selection_index = i
        selected.append(top_candidates[selection_index])
    
    return format_recommendations_for_display(selected)


def format_recommendations_for_display(recommendations):
    """
    Format recommendations for display in UI.
    
    Args:
        recommendations: List of recommendation dictionaries
    
    Returns:
        list: Formatted recommendations for display
    """
    formatted = []
    for rec in recommendations:
        formatted.append({
            'id': rec['id'],
            'username': rec['username'],
            'display_name': f"{rec['first_name']} {rec['last_name']}".strip() or rec['username'],
            'profile_picture_url': rec['profile_picture_url'],
            'photos_count': rec['photos_count'],
            'score': rec['score'],
            'is_private': rec.get('is_private', False)
        })
    
    return formatted


def update_recommendation_show_tracking(recommendations, user_id):
    """
    Update tracking information for shown recommendations.
    
    Args:
        recommendations: List of recommendations that were shown
        user_id: ID of the user
    """
    try:
        recommendation_ids = [rec['id'] for rec in recommendations]
        
        # Update tracking for shown recommendations
        from django.db import models
        UserRecommendation.objects.filter(
            user_id=user_id,
            recommended_user_id__in=recommendation_ids
        ).update(
            last_shown=timezone.now(),
            show_count=models.F('show_count') + 1
        )
        
    except Exception as e:
        logger.error(f"Error updating recommendation show tracking: {e}")


@shared_task(bind=True)
def trigger_recommendation_update_after_relationship_change(self, user_id, action_description):
    """
    Trigger recommendation update after a relationship change (follow/unfollow/request).
    
    Args:
        user_id: ID of the user whose recommendations need updating
        action_description: Description of the action that triggered the update
    """
    try:
        logger.info(f"Triggering recommendation update for user {user_id} after {action_description}")
        
        # Update recommendations for the user
        result = build_user_recommendations_for_user(user_id, top_k=30)
        
        if result.get('success'):
            logger.info(f"Successfully updated recommendations for user {user_id} after {action_description}")
            return f"Recommendations updated for user {user_id} after {action_description}"
        else:
            logger.warning(f"Failed to update recommendations for user {user_id}: {result.get('error')}")
            return f"Failed to update recommendations for user {user_id}"
            
    except Exception as exc:
        logger.error(f"Error updating recommendations after relationship change: {exc}")
        return f"Error updating recommendations: {exc}"


@shared_task(bind=True)
def cleanup_old_recommendations(self):
    """
    Clean up old recommendations that are no longer relevant.
    This runs periodically to maintain database performance.
    """
    try:
        from datetime import timedelta
        
        # Delete recommendations older than 7 days that haven't been shown recently
        cutoff_date = timezone.now() - timedelta(days=7)
        
        old_recommendations = UserRecommendation.objects.filter(
            created_at__lt=cutoff_date,
            last_shown__isnull=True  # Never shown
        )
        
        count = old_recommendations.count()
        old_recommendations.delete()
        
        logger.info(f"Cleaned up {count} old recommendations")
        return f"Cleaned up {count} old recommendations"
        
    except Exception as exc:
        logger.error(f"Error cleaning up old recommendations: {exc}")
        return f"Error cleaning up old recommendations: {exc}"