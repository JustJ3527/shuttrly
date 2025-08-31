"""
Utility functions for the posts app
"""

import re
from typing import List, Optional
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Post, PostLike, PostSave, PostComment
from photos.models import Photo, Collection

User = get_user_model()


def extract_hashtags_from_text(text: str) -> List[str]:
    """
    Extract hashtags from any text and return as a list
    
    Args:
        text (str): Text to extract hashtags from
        
    Returns:
        List[str]: List of hashtags without # symbol
    """
    if not text:
        return []
    
    hashtags = re.findall(r'#(\w+)', text)
    return list(dict.fromkeys(hashtags))  # Remove duplicates


def format_hashtags_for_display(tags: str) -> List[str]:
    """
    Format stored tags string for display
    
    Args:
        tags (str): Tags string from database (e.g., "#nature #city")
        
    Returns:
        List[str]: List of clean hashtags
    """
    if not tags:
        return []
    
    hashtags = [tag.strip() for tag in tags.split() if tag.strip().startswith('#')]
    return [tag[1:] for tag in hashtags]  # Remove # symbol


def format_hashtags_for_storage(tag_list: List[str]) -> str:
    """
    Format list of tags for storage in database
    
    Args:
        tag_list (List[str]): List of tags (with or without #)
        
    Returns:
        str: Formatted tags string for storage
    """
    hashtags = [f"#{tag.strip().lstrip('#')}" for tag in tag_list if tag.strip()]
    return " ".join(hashtags)


def create_post_from_photo(user, photo, description: str = "", visibility: str = "public") -> Post:
    """
    Create a single photo post
    
    Args:
        user: User creating the post
        photo: Photo object to post
        description (str): Post description with hashtags
        visibility (str): Post visibility
        
    Returns:
        Post: Created post object
    """
    content_type = ContentType.objects.get_for_model(Photo)
    
    post = Post.objects.create(
        author=user,
        description=description,
        post_type="single_photo",
        content_type=content_type,
        object_id=photo.id,
        visibility=visibility
    )
    
    return post


def create_post_from_collection(user, collection, description: str = "", visibility: str = "public") -> Post:
    """
    Create a collection post
    
    Args:
        user: User creating the post
        collection: Collection object to post
        description (str): Post description with hashtags
        visibility (str): Post visibility
        
    Returns:
        Post: Created post object
    """
    content_type = ContentType.objects.get_for_model(Collection)
    
    post = Post.objects.create(
        author=user,
        description=description,
        post_type="collection",
        content_type=content_type,
        object_id=collection.id,
        visibility=visibility
    )
    
    return post


def create_post_from_multiple_photos(user, photos: List[Photo], description: str = "", visibility: str = "public") -> Post:
    """
    Create a multiple photos post
    
    Args:
        user: User creating the post
        photos: List of Photo objects
        description (str): Post description with hashtags
        visibility (str): Post visibility
        
    Returns:
        Post: Created post object
    """
    # Use the first photo as content object for the generic foreign key
    first_photo = photos[0] if photos else None
    if not first_photo:
        raise ValueError("At least one photo is required")
    
    content_type = ContentType.objects.get_for_model(Photo)
    
    post = Post.objects.create(
        author=user,
        description=description,
        post_type="multiple_photos",
        content_type=content_type,
        object_id=first_photo.id,
        visibility=visibility
    )
    
    # Add all photos to the post
    post.photos.set(photos)
    
    return post


def update_post_description(post: Post, new_description: str) -> Post:
    """
    Update post description and automatically update tags
    
    Args:
        post: Post object to update
        new_description (str): New description with hashtags
        
    Returns:
        Post: Updated post object
    """
    post.update_description_with_tags(new_description)
    return post


def add_hashtag_to_post(post: Post, hashtag: str) -> Post:
    """
    Add a hashtag to a post's description
    
    Args:
        post: Post object to update
        hashtag (str): Hashtag to add (with or without #)
        
    Returns:
        Post: Updated post object
    """
    post.add_hashtag_to_description(hashtag)
    return post


def remove_hashtag_from_post(post: Post, hashtag: str) -> Post:
    """
    Remove a hashtag from a post's description
    
    Args:
        post: Post object to update
        hashtag (str): Hashtag to remove (with or without #)
        
    Returns:
        Post: Updated post object
    """
    post.remove_hashtag_from_description(hashtag)
    return post


def get_posts_by_hashtag(hashtag: str, user=None) -> List[Post]:
    """
    Get all posts containing a specific hashtag
    
    Args:
        hashtag (str): Hashtag to search for (with or without #)
        user: Optional user to filter by visibility
        
    Returns:
        List[Post]: List of posts with the hashtag
    """
    if not hashtag.startswith('#'):
        hashtag = f"#{hashtag}"
    
    posts = Post.objects.filter(tags__icontains=hashtag)
    
    # Filter by visibility if user is provided
    if user:
        posts = posts.filter(
            models.Q(visibility='public') |
            models.Q(author=user) |
            models.Q(visibility='friends', author__in=user.friends.all())
        )
    
    return posts.order_by('-published_at')


def get_trending_hashtags(limit: int = 10) -> List[dict]:
    """
    Get trending hashtags based on usage in posts
    
    Args:
        limit (int): Maximum number of hashtags to return
        
    Returns:
        List[dict]: List of trending hashtags with counts
    """
    from django.db.models import Count
    
    # Get all posts with tags
    posts_with_tags = Post.objects.exclude(tags='')
    
    # Extract hashtags and count them
    hashtag_counts = {}
    for post in posts_with_tags:
        hashtags = post.get_tags_list()
        for hashtag in hashtags:
            hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
    
    # Sort by count and return top hashtags
    trending = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {'hashtag': hashtag, 'count': count} 
        for hashtag, count in trending[:limit]
    ]


def validate_hashtag(hashtag: str) -> bool:
    """
    Validate if a hashtag is properly formatted: only letters and digits
    
    Args:
        hashtag (str): Hashtag to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not hashtag:
        return False
    
    # Remove # if present for validation
    clean_hashtag = hashtag.lstrip('#')
    
    # Check length
    if len(clean_hashtag) < 1 or len(clean_hashtag) > 50:
        return False
    
    # Check if contains only letters and digits
    if not re.match(r'^[a-zA-Z0-9]+$', clean_hashtag):
        return False
    
    return True


def suggest_hashtags(text: str, limit: int = 5) -> List[str]:
    """
    Suggest hashtags based on text content
    
    Args:
        text (str): Text to analyze
        limit (int): Maximum number of suggestions
        
    Returns:
        List[str]: List of suggested hashtags
    """
    # Simple keyword extraction (you could enhance this with NLP)
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common words and short words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word for word in words if len(word) > 2 and word not in common_words]
    
    # Count word frequency
    word_counts = {}
    for word in keywords:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Return top keywords as hashtags
    top_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [f"#{word}" for word, _ in top_keywords[:limit]]


# === POST ENGAGEMENT UTILITIES ===

def toggle_post_like(user: User, post: Post) -> dict:
    """
    Toggle like status for a post
    
    Args:
        user: User performing the action
        post: Post to like/unlike
        
    Returns:
        dict: Result with status and updated counts
    """
    try:
        existing_like = PostLike.objects.get(user=user, post=post)
        existing_like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save(update_fields=['likes_count'])
        
        return {
            'liked': False,
            'likes_count': post.likes_count,
            'message': 'Post unliked'
        }
    except PostLike.DoesNotExist:
        PostLike.objects.create(user=user, post=post)
        post.likes_count += 1
        post.save(update_fields=['likes_count'])
        
        return {
            'liked': True,
            'likes_count': post.likes_count,
            'message': 'Post liked'
        }


def toggle_post_save(user: User, post: Post) -> dict:
    """
    Toggle save status for a post
    
    Args:
        user: User performing the action
        post: Post to save/unsave
        
    Returns:
        dict: Result with status and updated counts
    """
    try:
        existing_save = PostSave.objects.get(user=user, post=post)
        existing_save.delete()
        post.saves_count = max(0, post.saves_count - 1)
        post.save(update_fields=['saves_count'])
        
        return {
            'saved': False,
            'saves_count': post.saves_count,
            'message': 'Post unsaved'
        }
    except PostSave.DoesNotExist:
        PostSave.objects.create(user=user, post=post)
        post.saves_count += 1
        post.save(update_fields=['saves_count'])
        
        return {
            'saved': True,
            'saves_count': post.saves_count,
            'message': 'Post saved'
        }


def add_post_comment(user: User, post: Post, content: str, parent_comment=None) -> PostComment:
    """
    Add a comment to a post
    
    Args:
        user: User adding the comment
        post: Post to comment on
        content: Comment content
        parent_comment: Optional parent comment for replies
        
    Returns:
        PostComment: Created comment object
    """
    comment = PostComment.objects.create(
        user=user,
        post=post,
        content=content,
        parent_comment=parent_comment
    )
    
    # Update post comment count
    post.comments_count += 1
    post.save(update_fields=['comments_count'])
    
    return comment


def delete_post_comment(user: User, comment: PostComment) -> dict:
    """
    Delete a comment from a post
    
    Args:
        user: User deleting the comment
        comment: Comment to delete
        
    Returns:
        dict: Result with status and updated counts
    """
    if comment.user != user:
        return {
            'success': False,
            'message': 'You can only delete your own comments'
        }
    
    post = comment.post
    comment.delete()
    
    # Update post comment count
    post.comments_count = max(0, post.comments_count - 1)
    post.save(update_fields=['comments_count'])
    
    return {
        'success': True,
        'message': 'Comment deleted',
        'comments_count': post.comments_count
    }


def increment_post_views(post: Post) -> None:
    """
    Increment view count for a post
    
    Args:
        post: Post to increment views for
    """
    post.increment_views()


def get_user_feed_posts(user: User, page: int = 1, per_page: int = 20) -> dict:
    """
    Get personalized feed posts for a user
    
    Args:
        user: User to get feed for
        page: Page number for pagination
        per_page: Posts per page
        
    Returns:
        dict: Feed data with posts and pagination info
    """
    from django.core.paginator import Paginator
    
    # Get posts based on user's preferences and following
    # For now, get public posts and user's own posts
    posts = Post.objects.filter(
        models.Q(visibility='public') |
        models.Q(author=user)
    ).select_related('author', 'content_type').prefetch_related('photos')
    
    # Order by engagement and recency
    posts = posts.annotate(
        engagement_score=models.F('likes_count') + models.F('comments_count') + models.F('views_count')
    ).order_by('-engagement_score', '-published_at')
    
    # Paginate results
    paginator = Paginator(posts, per_page)
    page_obj = paginator.get_page(page)
    
    return {
        'posts': page_obj,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page
    }


def get_post_statistics(post: Post) -> dict:
    """
    Get comprehensive statistics for a post
    
    Args:
        post: Post to get statistics for
        
    Returns:
        dict: Post statistics
    """
    return {
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'views_count': post.views_count,
        'saves_count': post.saves_count,
        'shares_count': post.shares_count,
        'engagement_rate': calculate_engagement_rate(post),
        'created_at': post.created_at,
        'published_at': post.published_at
    }


def calculate_engagement_rate(post: Post) -> float:
    """
    Calculate engagement rate for a post
    
    Args:
        post: Post to calculate engagement for
        
    Returns:
        float: Engagement rate as percentage
    """
    total_engagement = post.likes_count + post.comments_count + post.saves_count
    if post.views_count > 0:
        return round((total_engagement / post.views_count) * 100, 2)
    return 0.0


def get_user_post_stats(user: User) -> dict:
    """
    Get post statistics for a user
    
    Args:
        user: User to get stats for
        
    Returns:
        dict: User post statistics
    """
    user_posts = Post.objects.filter(author=user)
    
    total_posts = user_posts.count()
    total_likes = sum(post.likes_count for post in user_posts)
    total_comments = sum(post.comments_count for post in user_posts)
    total_views = sum(post.views_count for post in user_posts)
    
    return {
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_views': total_views,
        'average_engagement': round(total_likes / total_posts, 2) if total_posts > 0 else 0,
        'most_popular_post': user_posts.order_by('-likes_count').first()
    }