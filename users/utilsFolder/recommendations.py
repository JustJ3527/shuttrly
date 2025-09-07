import datetime
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from users.models import UserRelationship, UserRecommendation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def build_user_recommendations(top_k=10, friend_boost=1.2, following_boost=1.1, public_boost=0.8, follower_boost=0.5):
    """Batch job with cosine similarity + mutualfollow boost"""
    
    users = list(User.objects.all().order_by('-date_joined'))
    if len(users) < 2:
        logger.warning("Not enough users to generate recommendations")
        return
    
    user_index = {user.id: idx for idx, user in enumerate(users)}
    index_user = {idx: user.id for idx, user in enumerate(users)}
    
    # Create sparse matrix (user x follow)
    rows, cols = [], []
    for rel in UserRelationship.objects.filter(relationship_type="follow"):
        if rel.from_user_id in user_index and rel.to_user_id in user_index:
            rows.append(user_index[rel.from_user_id])
            cols.append(user_index[rel.to_user_id])

    n_users = len(users)
    
    if not rows:
        logger.warning("No follow relationships found, generating basic recommendations")
        # Generate basic recommendations based on user activity
        _generate_basic_recommendations(users, top_k)
        return
    
    mat = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_users, n_users))
    
    # Normalize the matrix
    mat_norm = normalize(mat, axis=0)
    
    # Calculate cosine similarity
    item_similarity = mat_norm.T @ mat_norm
    
    # Friend detection
    # A and B are friends if mat[A, B] == 1 and mat[B, A] == 1
    friend_pairs = (mat.multiply(mat.T)).nonzero()
    friend_set = set(zip(friend_pairs[0], friend_pairs[1]))
    
    # Erase old recommendations
    UserRecommendation.objects.filter(user__in=users).delete()
    
    recommendations = []
    for i in range(n_users):
        already_followed = set((mat[i].nonzero()[1]))
        
        if already_followed:
            # Use collaborative filtering
            scores = item_similarity[list(already_followed)].sum(axis=0).A1
        else:
            # If user follows no one, recommend popular users
            scores = np.ones(n_users) * 0.1  # Small base score for all users
        
        # Remove itself and already followed users
        scores[i] = 0
        for j in already_followed:
            scores[j] = 0
        
        # Boost scores for mutual friends
        for idx, score in enumerate(scores):
            if score > 0 and (i, idx) in friend_set:
                scores[idx] *= friend_boost
        
        # Add some randomness for diversity
        scores += np.random.random(n_users) * 0.01
        
        # Top k
        top_k_indices = np.argsort(-scores)[:top_k]
        for idx in top_k_indices:
            if scores[idx] > 0 and idx != i and idx not in already_followed:  # Exclude self and already followed users
                recommendations.append(UserRecommendation(
                    user_id=index_user[i],
                    recommended_user_id=index_user[idx],
                    score=float(scores[idx])
                ))
                
    # Bulk create recommendations
    with transaction.atomic():
        UserRecommendation.objects.bulk_create(recommendations, batch_size=5000)
    
    logger.info(f"Created {len(recommendations)} recommendations for {n_users} users")

def _generate_basic_recommendations(users, top_k=10):
    """Generate basic recommendations when there are no follow relationships"""
    UserRecommendation.objects.all().delete()
    
    recommendations = []
    for i, user in enumerate(users):
        # Get users already followed by this user
        already_followed_ids = set(user.get_following().values_list('id', flat=True))
        
        # Recommend other users based on simple criteria (excluding self and already followed)
        other_users = [u for j, u in enumerate(users) if j != i and u.id not in already_followed_ids]
        
        # Sort by activity (photos count, posts count, etc.)
        other_users.sort(key=lambda u: u.get_photos_count() + u.get_posts_count(), reverse=True)
        
        for j, other_user in enumerate(other_users[:top_k]):
            # Base score decreases with position
            base_score = 1.0 - (j * 0.1)
            
            # Boost score for users with more activity
            activity_boost = min(0.5, (other_user.get_photos_count() + other_user.get_posts_count()) * 0.01)
            
            # Add some randomness
            random_factor = np.random.random() * 0.2
            
            final_score = base_score + activity_boost + random_factor
            
            recommendations.append(UserRecommendation(
                user=user,
                recommended_user=other_user,
                score=final_score
            ))
    
    # Bulk create recommendations
    with transaction.atomic():
        UserRecommendation.objects.bulk_create(recommendations, batch_size=5000)
    
    logger.info(f"Created {len(recommendations)} basic recommendations for {len(users)} users")

def get_user_recommendations_cached(user_id, top_k=10, use_cache=True):
    """
    Get user recommendations with caching support.
    
    Args:
        user_id: ID of the user to get recommendations for
        top_k: Number of recommendations to return
        use_cache: Whether to use cache (default: True)
    
    Returns:
        list: List of recommended users with their details
    """
    if not use_cache:
        # Force recalculation
        from users.tasks import calculate_user_recommendations_task
        calculate_user_recommendations_task.delay(user_id, force_recalculate=True)
        return []
    
    # Try to get from cache first
    cache_key = f"user_recommendations_{user_id}"
    cached_recommendations = cache.get(cache_key)
    
    if cached_recommendations is not None:
        # Filter out deleted users from cached recommendations
        valid_recommendations = []
        for rec in cached_recommendations:
            try:
                # Check if the recommended user still exists
                User.objects.get(id=rec['id'], is_active=True, is_anonymized=False)
                valid_recommendations.append(rec)
            except User.DoesNotExist:
                print(f"⚠️ Removing deleted user {rec['username']} (ID: {rec['id']}) from cache")
                continue
        
        # If we filtered out users, update the cache
        if len(valid_recommendations) != len(cached_recommendations):
            cache.set(cache_key, valid_recommendations, timeout=86400)
            print(f"🔄 Updated cache for user {user_id}: {len(cached_recommendations)} -> {len(valid_recommendations)} recommendations")
        
        logger.debug(f"Retrieved {len(valid_recommendations)} recommendations from cache for user {user_id}")
        return valid_recommendations[:top_k]
    
    # If not in cache, try to get from database
    try:
        user = User.objects.get(id=user_id)
        recommendations = UserRecommendation.objects.filter(
            user=user
        ).select_related('recommended_user').order_by('-score')[:top_k]
        
        if recommendations.exists():
            # Convert to list format and cache, filtering out inactive users
            recommendations_list = []
            invalid_recommendation_ids = []
            
            for rec in recommendations:
                recommended_user = rec.recommended_user
                
                # Check if recommended user is still active
                if not recommended_user.is_active or recommended_user.is_anonymized:
                    print(f"⚠️ Found inactive recommended user: {recommended_user.username} (ID: {recommended_user.id})")
                    invalid_recommendation_ids.append(rec.id)
                    continue
                
                recommendations_list.append({
                    'id': recommended_user.id,
                    'username': recommended_user.username,
                    'first_name': recommended_user.first_name,
                    'last_name': recommended_user.last_name,
                    'profile_picture_url': recommended_user.profile_picture.url if recommended_user.profile_picture else None,
                    'is_private': recommended_user.is_private,
                    'photos_count': recommended_user.get_photos_count(),
                    'score': rec.score
                })
            
            # Clean up invalid recommendations from database
            if invalid_recommendation_ids:
                UserRecommendation.objects.filter(id__in=invalid_recommendation_ids).delete()
                print(f"🧹 Cleaned up {len(invalid_recommendation_ids)} invalid recommendations from database")
            
            # Cache for 24 hours
            cache.set(cache_key, recommendations_list, timeout=86400)
            logger.info(f"Retrieved {len(recommendations_list)} recommendations from database for user {user_id}")
            return recommendations_list
        else:
            # No recommendations in database, trigger background calculation
            from users.tasks import calculate_user_recommendations_task
            calculate_user_recommendations_task.delay(user_id)
            logger.info(f"No recommendations found for user {user_id}, triggered background calculation")
            return []
            
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return []
    except Exception as exc:
        logger.error(f"Error getting recommendations for user {user_id}: {exc}")
        return []

def get_recommendations_for_display(user_id, limit=5):
    """
    Get recommendations formatted for display in UI.
    
    Args:
        user_id: ID of the user to get recommendations for
        limit: Number of recommendations to return (default: 5)
    
    Returns:
        list: List of recommended users formatted for display
    """
    recommendations = get_user_recommendations_cached(user_id, top_k=limit * 2)  # Get more to filter
    
    # Get current user's following list to filter out
    try:
        user = User.objects.get(id=user_id)
        user_following = set(user.get_following().values_list('id', flat=True))
        print(f"🔍 DEBUG: User {user.username} follows {len(user_following)} users: {list(user_following)}")
    except User.DoesNotExist:
        print(f"❌ User with ID {user_id} not found")
        return []
    
    # Filter out private users, deleted users, and users already followed
    display_recommendations = []
    for rec in recommendations:
        # Skip if already following
        if rec['id'] in user_following:
            print(f"🔍 DEBUG: Skipping {rec['username']} (already following)")
            continue
            
        # Verify the recommended user still exists and is active
        try:
            recommended_user = User.objects.get(
                id=rec['id'],
                is_active=True,
                is_anonymized=False
            )
            
            display_recommendations.append({
                'id': rec['id'],
                'username': rec['username'],
                'display_name': f"{rec['first_name']} {rec['last_name']}".strip() or rec['username'],
                'profile_picture_url': rec['profile_picture_url'],
                'photos_count': rec['photos_count'],
                'score': rec['score'],
                'is_private': rec.get('is_private', False)
            })
            
            # Stop when we have enough recommendations
            if len(display_recommendations) >= limit:
                break
                
        except User.DoesNotExist:
            # User was deleted, skip this recommendation
            print(f"⚠️ Skipping deleted user {rec['username']} (ID: {rec['id']}) from recommendations")
            continue
    
    print(f"🔍 DEBUG: Returning {len(display_recommendations)} recommendations for display")
    return display_recommendations


def build_user_recommendations_for_user(user_id, top_k=10, friend_boost=1.2, following_boost=1.1, public_boost=0.8, follower_boost=0.5):
    """
    Build recommendations for a specific user only.
    
    Args:
        user_id: ID of the user to build recommendations for
        top_k: Number of top recommendations to keep
        friend_boost: Boost factor for mutual friends
        following_boost: Boost factor for users following the same people
        public_boost: Boost factor for public users
        follower_boost: Boost factor for users with similar followers
    
    Returns:
        dict: Results of the recommendation building
    """
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print(f"❌ User with ID {user_id} not found")
            return {"success": False, "error": "User not found"}
        
        print(f"🔄 Building recommendations for user: {user.username} (ID: {user_id})")
        
        # Get all users except the current user
        all_users = User.objects.filter(is_active=True, is_anonymized=False).exclude(id=user_id)
        
        print(f"🔍 DEBUG: Found {all_users.count()} potential candidates")
        print(f"🔍 DEBUG: User list: {[u.username for u in all_users[:10]]}...")  # Show first 10
        
        if all_users.count() < 1:
            print(f"⚠️ Not enough users to build recommendations (only {all_users.count()} other users)")
            return {"success": False, "error": "Not enough users"}
        
        # Get user's relationships
        user_following = set(user.get_following().values_list('id', flat=True))
        user_followers = set(user.get_followers().values_list('id', flat=True))
        user_friends = set(user.get_friends().values_list('id', flat=True))
        
        print(f"📊 User {user.username} stats: {len(user_following)} following, {len(user_followers)} followers, {len(user_friends)} friends")
        print(f"🔍 DEBUG: User follows: {list(user_following)}")
        
        # Calculate recommendations for this specific user
        recommendations = []
        candidates_analyzed = 0
        candidates_skipped_following = 0
        candidates_zero_score = 0
        
        for other_user in all_users:
            if other_user.id == user_id:
                continue
                
            # Skip if already following
            if other_user.id in user_following:
                candidates_skipped_following += 1
                print(f"🔍 DEBUG: Skipping {other_user.username} (already following)")
                continue
            
            candidates_analyzed += 1
            print(f"🔍 DEBUG: Analyzing candidate #{candidates_analyzed}: {other_user.username}")
            
            score = 0.0
            
            # Debug info for this candidate
            print(f"\n🔍 DETAILED SCORE DEBUG: {user.username} -> {other_user.username}")
            
            # Start with base score of 0.5 for better distribution
            score = 0.5
            print(f"   📊 Base score: {score:.4f}")
            
            # Get other user's relationships
            other_following = set(other_user.get_following().values_list('id', flat=True))
            other_followers = set(other_user.get_followers().values_list('id', flat=True))
            
            # Recent Activity boost (time-weighted) - HIGHEST PRIORITY
            recent_activity_score = _get_recent_activity_score(other_user)
            old_score = score
            
            if recent_activity_score > 0:
                # Recent activity is the TOP factor: up to 10x multiplier
                recent_multiplier = 1 + (recent_activity_score * 9.0)  # 1.0 to 10.0x
                score *= recent_multiplier
                print(f"   🔥 Recent Activity: {recent_activity_score:.3f} score → Score: {old_score:.4f} → {score:.4f} (×{recent_multiplier:.2f})")
            else:
                print(f"   🔥 Recent Activity: No recent activity → No boost")
            
            # Total Activity boost (posts + photos) - SECOND PRIORITY
            photos_count = other_user.get_photos_count()
            posts_count = other_user.get_posts_count()
            total_activity = (posts_count * 2) + photos_count
            old_score = score
            
            if total_activity > 0:
                # Total activity factor: up to 3x multiplier (reduced from 5x since recent activity is priority)
                activity_multiplier = 1 + min(total_activity / 100.0, 2.0)  # 1.0 to 3.0x
                score *= activity_multiplier
                print(f"   📸 Total Activity: {posts_count} posts + {photos_count} photos (total: {total_activity}) → Score: {old_score:.4f} → {score:.4f} (×{activity_multiplier:.2f})")
            else:
                print(f"   📸 Total Activity: 0 posts + 0 photos → No boost")
            
            # Mutual friends boost (second most important)
            mutual_friends = len(user_friends.intersection(set(other_user.get_friends().values_list('id', flat=True))))
            old_score = score
            if mutual_friends > 0:
                friend_multiplier = 1 + (mutual_friends * 0.3)  # +30% per mutual friend
                score *= friend_multiplier
                print(f"   🤝 Mutual Friends: {mutual_friends} friends → Score: {old_score:.4f} → {score:.4f} (×{friend_multiplier:.2f})")
            else:
                print(f"   🤝 Mutual Friends: 0 friends → No boost")
            
            # Following same people boost
            common_following = len(user_following.intersection(other_following))
            old_score = score
            if common_following > 0:
                following_multiplier = 1 + (common_following * 0.1)  # +10% per common follow
                score *= following_multiplier
                print(f"   👥 Common Following: {common_following} users → Score: {old_score:.4f} → {score:.4f} (×{following_multiplier:.2f})")
            else:
                print(f"   👥 Common Following: 0 users → No boost")
            
            # Public/Private account factor (no penalty for private accounts)
            old_score = score
            if not other_user.is_private:
                public_multiplier = 1.1  # Small boost for public (10%)
                score *= public_multiplier
                print(f"   🌍 Public Account: Yes → Score: {old_score:.4f} → {score:.4f} (×{public_multiplier:.2f})")
            else:
                # No penalty for private accounts - they should be equally recommended
                print(f"   🔒 Private Account: Yes → No penalty (equal treatment)")
            
            # Similar followers boost
            common_followers = len(user_followers.intersection(other_followers))
            old_score = score
            if common_followers > 0:
                follower_multiplier = 1 + (common_followers * 0.05)  # +5% per common follower
                score *= follower_multiplier
                print(f"   📱 Common Followers: {common_followers} users → Score: {old_score:.4f} → {score:.4f} (×{follower_multiplier:.2f})")
            else:
                print(f"   📱 Common Followers: 0 users → No boost")
            
            # New account boost (smallest impact)
            days_since_joined = (datetime.datetime.now().date() - other_user.date_joined.date()).days
            old_score = score
            if days_since_joined <= 30:
                new_account_factor = max(0, (30 - days_since_joined) / 30)
                new_account_multiplier = 1 + (new_account_factor * 0.1)  # Max 10% boost
                score *= new_account_multiplier
                print(f"   🆕 New Account: {days_since_joined} days old → Score: {old_score:.4f} → {score:.4f} (×{new_account_multiplier:.2f})")
            else:
                print(f"   🗓️ Old Account: {days_since_joined} days old → No boost")
            
            # Normalize score to 0-1 range
            # With recent activity (10x) + total activity (3x) + friends + public, max ~40
            # Normalize to 0-1 range with better distribution
            # Use a more reasonable normalization that gives scores in 0.2-0.9 range
            score = min(score / 3.0, 1.0)  # Divide by 3 for better score distribution (0.2-0.9 range)
            
            print(f"   📈 FINAL SCORE: {score:.4f}")
            print(f"   👤 Candidate info: {other_user.username} ({'Private' if other_user.is_private else 'Public'}, {photos_count} photos, {days_since_joined} days old)")
            print("   " + "-" * 60)
            
            if score > 0:
                print(f"✅ DEBUG: {other_user.username} qualified with score {score:.4f}")
                recommendations.append({
                    'user_id': other_user.id,
                    'score': score,
                    'username': other_user.username,
                    'is_private': other_user.is_private,
                    'photos_count': photos_count
                })
            else:
                candidates_zero_score += 1
                print(f"❌ DEBUG: {other_user.username} has zero score")
        
        # Sort by score and take top_k
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = recommendations[:top_k]
        
        print(f"📊 DEBUG SUMMARY for {user.username}:")
        print(f"   - Total potential candidates: {all_users.count()}")
        print(f"   - Skipped (already following): {candidates_skipped_following}")
        print(f"   - Analyzed: {candidates_analyzed}")
        print(f"   - Zero score: {candidates_zero_score}")
        print(f"   - Qualified: {len(recommendations)}")
        print(f"   - Final recommendations: {len(top_recommendations)}")
        print(f"✅ Generated {len(top_recommendations)} recommendations for {user.username}")
        
        # Save to database
        from users.models import UserRecommendation
        
        # Delete existing recommendations for this user
        UserRecommendation.objects.filter(user=user).delete()
        
        # Create new recommendations
        for rec in top_recommendations:
            UserRecommendation.objects.create(
                user=user,
                recommended_user_id=rec['user_id'],
                score=rec['score']
            )
        
        print(f"💾 Saved {len(top_recommendations)} recommendations to database for {user.username}")
        
        return {
            "success": True,
            "user_id": user_id,
            "username": user.username,
            "recommendations_count": len(top_recommendations),
            "recommendations": top_recommendations
        }
        
    except Exception as e:
        print(f"❌ Error building recommendations for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def calculate_user_photo_similarity(user1, user2):
    """
    Calculate photo similarity between two users using their CLIP embeddings.

    Args:
        user1: First user object
        user2: Second user object

    Returns:
        float: Photo similarity score between 0 and 1
    """
    try:
        from photos.models import Photo
        from photos.utils import calculate_cosine_similarity

        # Safety check to avoid errors
        if not hasattr(user1, 'id') or not hasattr(user2, 'id'):
            return 0.0

        photos1 = Photo.objects.filter(user=user1, embedding__isnull=False)[:10]
        photos2 = Photo.objects.filter(user=user2, embedding__isnull=False)[:10]

        if not photos1.exists() or not photos2.exists():
            return 0.0

        # Calculate middle similarity between all pairs of photos
        total_similarity = 0.0
        pair_count = 0

        for photo1 in photos1:
            for photo2 in photos2:
                try:
                    similarity = calculate_cosine_similarity(photo1, photo2)
                    if similarity is not None:
                        total_similarity += similarity
                        pair_count += 1
                except Exception as sim_error:
                    print(f"⚠️ Error calculating similarity for photos {photo1.id}-{photo2.id}: {sim_error}")
                    continue

        if pair_count == 0:
            return 0.0

        return total_similarity / pair_count
        
    except ImportError as ie:
        print(f"⚠️ Import error in photo similarity calculation: {ie}")
        return 0.0
    except Exception as e:
        print(f"⚠️ Error calculating photo similarity between {user1.username} and {user2.username}: {e}")
        return 0.0

def build_user_recommendations_with_boosts(top_k=10, friend_boost=1.2, following_boost=1.1, public_boost=0.8, follower_boost=0.5, photo_similarity_boost=1.1, new_account_boost=0.2):
    """
    Build user recommendations with enhanced boost factors including photo similarity.

    Args:
        top_k: Number of recommendations to generate
        friend_boost: Boost factor for mutual friends
        following_boost: Boost factor for users you follow
        public_boost: Boost factor for public accounts
        follower_boost: Boost factor for users who follow you
        photo_similarity_boost: Boost factor for photo similarity
        new_account_boost: Boost factor for new accounts (recently joined) - reduced to 0.2
    
    Returns:
        list: List of recommended users with scores
    """
    from datetime import datetime, timedelta
    
    users = list(User.objects.filter(is_active=True, is_anonymized=False).order_by('-date_joined'))

    if len(users) < 2:
        logger.warning("Not enough users to generate enhanced recommendations")
        return []

    # Calculate similarity matrix for all users
    similarity_matrix = {}
    for i, user1 in enumerate(users):
        for j, user2 in enumerate(users[i+1:], i+1):
            # Calculate collaborative filtering similarity
            similarity = _calculate_collaborative_similarity(user1, user2)
            similarity_matrix[(user1.id, user2.id)] = similarity
            similarity_matrix[(user2.id, user1.id)] = similarity

    # Generate recommendations for each user
    recommendations = []
    for user in users:
        user_recommendations = []

        for candidate in users:
            if candidate.id == user.id:
                continue

            # Skip if already following
            if user.is_following(candidate):
                continue

            # Get base similarity score
            similarity = similarity_matrix.get((user.id, candidate.id), 0.0)

            if similarity <= 0.0:
                continue

            # Initialize score with base similarity
            score = similarity
            score_debug = {
                'user': user.username,
                'candidate': candidate.username,
                'base_similarity': similarity,
                'score_steps': [],
                'final_score': 0.0
            }

            # 1. Mutual friends boost
            mutual_friends = _get_mutual_friends_count(user, candidate)
            old_score = score
            if mutual_friends > 0:
                boost_factor = (1 + (mutual_friends * 0.1) * friend_boost)
                score *= boost_factor
                score_debug['score_steps'].append({
                    'step': '1. Mutual Friends',
                    'count': mutual_friends,
                    'boost_factor': boost_factor,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"+{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '1. Mutual Friends',
                    'count': 0,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # 2. Following boost (if user follows candidate) - Skip this as they already follow
            # This condition is already handled above
            
            # 3. Public account boost
            old_score = score
            if not candidate.is_private:
                score *= public_boost
                score_debug['score_steps'].append({
                    'step': '3. Public Account',
                    'is_public': True,
                    'boost_factor': public_boost,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '3. Public Account',
                    'is_public': False,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # 4. Follower boost (if candidate follows user)
            old_score = score
            if candidate.is_following(user):
                score *= follower_boost
                score_debug['score_steps'].append({
                    'step': '4. Follower',
                    'follows_back': True,
                    'boost_factor': follower_boost,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '4. Follower',
                    'follows_back': False,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })
            
            # 5. Photo similarity boost
            photo_similarity = calculate_user_photo_similarity(user, candidate)
            old_score = score
            if photo_similarity > 0.0:
                boost_factor = (1 + photo_similarity * photo_similarity_boost)
                score *= boost_factor
                score_debug['score_steps'].append({
                    'step': '5. Photo Similarity',
                    'similarity_score': photo_similarity,
                    'boost_factor': boost_factor,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"+{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '5. Photo Similarity',
                    'similarity_score': 0.0,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # 6. New account boost (accounts created in the last 30 days)
            days_since_joined = (datetime.now().date() - candidate.date_joined.date()).days
            old_score = score
            if days_since_joined <= 30:
                new_account_factor = max(0, (30 - days_since_joined) / 30)  # 1.0 for today, 0.0 for 30 days ago
                boost_factor = (1 + new_account_factor * new_account_boost)
                score *= boost_factor
                score_debug['score_steps'].append({
                    'step': '6. New Account',
                    'days_since_joined': days_since_joined,
                    'is_new_account': True,
                    'new_account_factor': new_account_factor,
                    'boost_factor': boost_factor,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"+{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '6. New Account',
                    'days_since_joined': days_since_joined,
                    'is_new_account': False,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # 7. Activity boost (posts + photos, posts weighted higher)
            photo_count = candidate.get_photos_count()
            posts_count = candidate.get_posts_count()
            old_score = score
            
            # Posts are more valuable than photos (2x weight)
            total_activity = (posts_count * 2) + photo_count
            
            if total_activity > 0:
                activity_factor = min(1.0, total_activity / 200)  # Cap at 200 activity points
                boost_factor = (1 + activity_factor * 0.5)  # Stronger boost for activity (0.5 instead of 0.1)
                score *= boost_factor
                score_debug['score_steps'].append({
                    'step': '7. Activity',
                    'posts_count': posts_count,
                    'photo_count': photo_count,
                    'total_activity': total_activity,
                    'activity_factor': activity_factor,
                    'boost_factor': boost_factor,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"+{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '7. Activity',
                    'posts_count': 0,
                    'photo_count': 0,
                    'total_activity': 0,
                    'activity_factor': 0.0,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # 8. Recent activity boost (photos/posts in the last 30 days)
            recent_activity = _get_recent_activity_score(candidate)
            old_score = score
            if recent_activity > 0:
                boost_factor = (1 + recent_activity * 0.2)  # Boost for recent activity
                score *= boost_factor
                score_debug['score_steps'].append({
                    'step': '8. Recent Activity',
                    'recent_activity_score': recent_activity,
                    'boost_factor': boost_factor,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': f"+{((score/old_score - 1) * 100):.1f}%"
                })
            else:
                score_debug['score_steps'].append({
                    'step': '8. Recent Activity',
                    'recent_activity_score': 0.0,
                    'boost_factor': 1.0,
                    'score_before': old_score,
                    'score_after': score,
                    'improvement': "0%"
                })

            # Final score
            score_debug['final_score'] = score
            score_debug['total_improvement'] = f"+{((score/similarity - 1) * 100):.1f}%" if similarity > 0 else "N/A"
            
            # Log detailed debug info
            print(f"\n🔍 SCORE DEBUG: {user.username} -> {candidate.username}")
            print(f"   📊 Base similarity: {similarity:.4f}")
            print(f"   📈 Final score: {score:.4f} (Total improvement: {score_debug['total_improvement']})")
            print(f"   👤 Candidate info: {candidate.username} ({'Private' if candidate.is_private else 'Public'}, {photo_count} photos, {days_since_joined} days old)")
            print("   🔢 Step-by-step breakdown:")
            for step in score_debug['score_steps']:
                print(f"      {step['step']}: {step['improvement']} (factor: {step['boost_factor']:.3f})")
            print("   " + "-" * 70)

            user_recommendations.append({
                'user': candidate,
                'score': score,
                'similarity': similarity,
                'mutual_friends': mutual_friends,
                'photo_similarity': photo_similarity,
                'is_new_account': days_since_joined <= 30,
                'photo_count': photo_count,
                'recent_activity': recent_activity
            })

        # Sort by score and take top_k
        user_recommendations.sort(key=lambda x: x['score'], reverse=True)
        user_recommendations = user_recommendations[:top_k]

        recommendations.extend(user_recommendations)

    return recommendations


def _calculate_collaborative_similarity(user1, user2):
    """
    Calculate collaborative filtering similarity between two users.
    
    Args:
        user1: First user object
        user2: Second user object
    
    Returns:
        float: Similarity score between 0 and 1
    """
    # Get users that user1 follows
    following1 = set(user1.get_following().values_list('id', flat=True))
    
    # Get users that user2 follows
    following2 = set(user2.get_following().values_list('id', flat=True))
    
    if not following1 and not following2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(following1.intersection(following2))
    union = len(following1.union(following2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def _get_mutual_friends_count(user1, user2):
    """
    Get count of mutual friends between two users.
    
    Args:
        user1: First user object
        user2: Second user object
    
    Returns:
        int: Number of mutual friends
    """
    following1 = set(user1.get_following().values_list('id', flat=True))
    following2 = set(user2.get_following().values_list('id', flat=True))
    
    return len(following1.intersection(following2))


def _get_recent_activity_score(user):
    """
    Calculate recent activity score for a user using time-weighted scoring.
    More recent activity gets higher weight.
    
    Args:
        user: User object
    
    Returns:
        float: Activity score between 0 and 1, weighted by recency
    """
    from datetime import timedelta
    from photos.models import Photo
    from posts.models import Post
    
    now = datetime.datetime.now().date()
    
    # Time periods with decreasing weights (more recent = higher weight)
    time_periods = [
        (1, 5.0),      # Last 1 day: 5x weight
        (7, 3.0),      # Last week: 3x weight
        (14, 2.0),     # Last 2 weeks: 2x weight
        (21, 1.5),     # Last 3 weeks: 1.5x weight
        (30, 1.0),     # Last month: 1x weight
    ]
    
    total_weighted_score = 0.0
    
    for days_back, weight in time_periods:
        period_start = now - timedelta(days=days_back)
        
        # Count photos in this period
        try:
            period_photos = Photo.objects.filter(
                user=user,
                created_at__date__gte=period_start,
                created_at__date__lt=(now - timedelta(days=days_back-1) if days_back > 1 else now + timedelta(days=1))
            ).count()
        except:
            period_photos = 0
        
        # Count posts in this period (worth 2x photos)
        try:
            period_posts = Post.objects.filter(
                author=user,
                created_at__date__gte=period_start,
                created_at__date__lt=(now - timedelta(days=days_back-1) if days_back > 1 else now + timedelta(days=1))
            ).count()
        except:
            period_posts = 0
        
        # Posts worth 2x photos, weighted by recency
        period_activity = (period_posts * 2) + period_photos
        weighted_activity = period_activity * weight
        total_weighted_score += weighted_activity
    
    # Normalize to 0-1 range (cap at 100 weighted points)
    return min(1.0, total_weighted_score / 100.0)


def calculate_user_photo_similarity_cached(user1, user2):
    """
    Calculate photo similarity between two users with caching.
    
    Args:
        user1: First user object
        user2: Second user object
    
    Returns:
        float: Photo similarity score between 0 and 1
    """
    try:
        # Check if photo similarity is globally enabled
        from django.core.cache import cache
        is_enabled = cache.get('photo_similarity_enabled', True)
        if not is_enabled:
            return 0.0
            
        # Create cache key
        cache_key = f"photo_similarity_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
        
        # Check cache first
        cached_score = cache.get(cache_key)
        if cached_score is not None:
            return cached_score
        
        # Quick check if users have photos with embeddings before heavy calculation
        try:
            from photos.models import Photo
            user1_has_embeddings = Photo.objects.filter(
                user=user1, 
                embedding__isnull=False
            ).exists()
            user2_has_embeddings = Photo.objects.filter(
                user=user2, 
                embedding__isnull=False
            ).exists()
            
            if not user1_has_embeddings or not user2_has_embeddings:
                # Cache the zero result to avoid repeated checks
                cache.set(cache_key, 0.0, 3600)
                return 0.0
                
        except Exception as check_error:
            print(f"⚠️ Error checking embeddings existence: {check_error}")
            cache.set(cache_key, 0.0, 3600)
            return 0.0
        
        # Calculate similarity if not cached and users have embeddings
        similarity = calculate_user_photo_similarity(user1, user2)
        
        # Cache for 1 hour
        cache.set(cache_key, similarity, 3600)
        
        return similarity
        
    except Exception as e:
        print(f"⚠️ Error in cached photo similarity calculation: {e}")
        return 0.0


def get_user_recommendations_with_enhanced_boosts(user_id, top_k=10):
    """
    Get recommendations for a specific user with all boost factors.
    
    Args:
        user_id: ID of the user to get recommendations for
        top_k: Number of recommendations to return
    
    Returns:
        list: List of recommended users with detailed scores
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return []
    
    # Get all recommendations with enhanced boosts
    all_recommendations = build_user_recommendations_with_boosts(
        top_k=top_k * 2,  # Get more to filter
        friend_boost=1.2,
        following_boost=1.1,
        public_boost=0.8,
        follower_boost=0.5,
        photo_similarity_boost=1.1,
        new_account_boost=0.2
    )
    
    # Filter for this specific user and format for display
    user_recommendations = []
    for rec in all_recommendations:
        if rec.get('user') and hasattr(rec['user'], 'id'):
            user_recommendations.append({
                'id': rec['user'].id,
                'username': rec['user'].username,
                'first_name': rec['user'].first_name,
                'last_name': rec['user'].last_name,
                'profile_picture_url': rec['user'].profile_picture.url if rec['user'].profile_picture else None,
                'is_private': rec['user'].is_private,
                'photos_count': rec.get('photo_count', 0),
                'score': rec['score'],
                'similarity': rec.get('similarity', 0),
                'mutual_friends': rec.get('mutual_friends', 0),
                'photo_similarity': rec.get('photo_similarity', 0),
                'is_new_account': rec.get('is_new_account', False),
                'recent_activity': rec.get('recent_activity', 0)
            })
    
    # Sort and return top recommendations
    user_recommendations.sort(key=lambda x: x['score'], reverse=True)
    return user_recommendations[:top_k]


def debug_user_recommendations(user_id, detailed=True):
    """
    Debug function to understand why a user has few recommendations.
    
    Args:
        user_id: ID of the user to debug
        detailed: Whether to show detailed analysis
    
    Returns:
        dict: Debug information
    """
    try:
        user = User.objects.get(id=user_id)
        all_users = User.objects.filter(is_active=True, is_anonymized=False).exclude(id=user_id)
        
        print(f"\n🔍 DEBUG ANALYSIS for {user.username} (ID: {user_id})")
        print("=" * 60)
        
        # Check user stats
        user_following = set(user.get_following().values_list('id', flat=True))
        user_followers = set(user.get_followers().values_list('id', flat=True))
        user_friends = set(user.get_friends().values_list('id', flat=True))
        
        print(f"👤 User stats:")
        print(f"   - Following: {len(user_following)} users")
        print(f"   - Followers: {len(user_followers)} users")
        print(f"   - Friends: {len(user_friends)} users")
        print(f"   - Photos: {user.get_photos_count()}")
        print(f"   - Account age: {(datetime.datetime.now().date() - user.date_joined.date()).days} days")
        print(f"   - Private: {user.is_private}")
        
        # Check potential candidates
        print(f"\n📊 Potential candidates:")
        print(f"   - Total users in system: {User.objects.count()}")
        print(f"   - Active users: {User.objects.filter(is_active=True).count()}")
        print(f"   - Non-anonymized: {User.objects.filter(is_anonymized=False).count()}")
        print(f"   - Excluding self: {all_users.count()}")
        print(f"   - Already following: {len(user_following)}")
        print(f"   - Available to recommend: {all_users.count() - len(user_following)}")
        
        # Check specific candidates
        candidates_analysis = []
        for other_user in all_users[:5]:  # Check first 5
            if other_user.id in user_following:
                continue
                
            # Calculate score factors
            mutual_friends = len(set(user_friends).intersection(set(other_user.get_friends().values_list('id', flat=True))))
            common_following = len(user_following.intersection(set(other_user.get_following().values_list('id', flat=True))))
            common_followers = len(user_followers.intersection(set(other_user.get_followers().values_list('id', flat=True))))
            
            candidate_info = {
                'username': other_user.username,
                'is_private': other_user.is_private,
                'photos_count': other_user.get_photos_count(),
                'days_old': (datetime.datetime.now().date() - other_user.date_joined.date()).days,
                'mutual_friends': mutual_friends,
                'common_following': common_following,
                'common_followers': common_followers,
                'follows_back': other_user.is_following(user)
            }
            
            candidates_analysis.append(candidate_info)
        
        print(f"\n👥 Sample candidates analysis:")
        for i, candidate in enumerate(candidates_analysis, 1):
            print(f"   {i}. {candidate['username']}:")
            print(f"      - Private: {candidate['is_private']}")
            print(f"      - Photos: {candidate['photos_count']}")
            print(f"      - Days old: {candidate['days_old']}")
            print(f"      - Mutual friends: {candidate['mutual_friends']}")
            print(f"      - Common following: {candidate['common_following']}")
            print(f"      - Common followers: {candidate['common_followers']}")
            print(f"      - Follows back: {candidate['follows_back']}")
        
        # Recommendations
        print(f"\n🎯 Recommendations to improve:")
        if len(user_following) == 0:
            print("   ⚠️ User follows nobody - recommendations based only on basic factors")
        if len(user_followers) == 0:
            print("   ⚠️ User has no followers - missing follower boost")
        if user.get_photos_count() == 0:
            print("   ⚠️ User has no photos - missing photo similarity boost")
        if all_users.count() < 5:
            print("   ⚠️ Very few users in system - limited recommendation pool")
            
        return {
            'user_stats': {
                'following': len(user_following),
                'followers': len(user_followers),
                'friends': len(user_friends),
                'photos': user.get_photos_count(),
                'age_days': (datetime.datetime.now().date() - user.date_joined.date()).days
            },
            'candidate_pool': {
                'total_users': all_users.count(),
                'already_following': len(user_following),
                'available': all_users.count() - len(user_following)
            },
            'sample_candidates': candidates_analysis
        }
        
    except Exception as e:
        print(f"❌ Error in debug analysis: {e}")
        return {'error': str(e)}