"""
Models for the posts app
"""

# Django imports
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import re

# Local imports
from photos.models import Photo


User = get_user_model()


class Post(models.Model):
    """Social post model for sharing photos and collections"""

    POST_TYPES = [
        ("single_photo", "Single Photo"),
        ("multiple_photos", "Multiple Photos"),
        ("collection", "Collection"),
    ]

    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
        ("friends", "Friends"),
    ]

    # Basic post information
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True, help_text="Description of the post")
    tags = models.CharField(max_length=500, blank=True, help_text="Tags for the post (hashtags)")

    # Post type and content
    post_type = models.CharField(max_length=20, choices=POST_TYPES)

    # Content relationships (Generic Foreign Key approach)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # For multiple photos posts
    photos = models.ManyToManyField(Photo, blank=True, related_name="posts")

    # Privacy and visibility
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default="public")
    is_featured = models.BooleanField(default=False)

    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    saves_count = models.PositiveIntegerField(default=0)

    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(auto_now_add=True)    
    
    class Meta:
        ordering = ["-published_at", "created_at"]
        indexes = [
            models.Index(fields=["author", "published_at"]),
            models.Index(fields=["post_type", "-published_at"]),
            models.Index(fields=["visibility", "-published_at"]),
            models.Index(fields=["tags"])
        ]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return f"{self.author.username} - {self.get_post_type_display()} - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically extract tags from description"""
        if self.description:
            self.tags = self.extract_hashtags_from_description()
        super().save(*args, **kwargs)

    def extract_hashtags_from_description(self):
        """Extract hashtags from the description and return as space-separated string"""
        if not self.description:
            return ""
        
        # Find all hashtags in the description
        hashtags = re.findall(r"#\w+", self.description)
        # Remove duplicates and join with spaces
        unique_hashtags = list(dict.fromkeys(hashtags))
        return " ".join(unique_hashtags)
    
    def get_tags_list(self):
        """Return tags as a list of strings"""
        if self.tags:
            hashtags = [tag.strip() for tag in self.tags.split() if tag.strip().startswith("#")]
            return [tag[1:] for tag in hashtags] # Remove # symbol
        return []

    def update_description_with_tags(self, new_description):
        """Update description and automatically update tags"""
        self.description = new_description
        self.save()  # This will trigger the save() method and update tags
    
    def add_hashtag_to_description(self, hashtag):
        """Add a hashtag to the description (and thus to tags)"""
        if not hashtag.startswith('#'):
            hashtag = f"#{hashtag}"
        
        # Add hashtag to description if not already present
        if hashtag not in (self.description or ""):
            current_desc = self.description or ""
            new_desc = f"{current_desc} {hashtag}".strip()
            self.update_description_with_tags(new_desc)
    
    def remove_hashtag_from_description(self, hashtag):
        """Remove a hashtag from the description (and thus from tags)"""
        if not hashtag.startswith('#'):
            hashtag = f"#{hashtag}"
        
        if self.description and hashtag in self.description:
            # Remove the hashtag from description
            new_desc = re.sub(rf'\s*{re.escape(hashtag)}\s*', ' ', self.description)
            new_desc = re.sub(r'\s+', ' ', new_desc).strip()  # Clean up extra spaces
            self.update_description_with_tags(new_desc)
    
    def replace_hashtag_in_description(self, old_hashtag, new_hashtag):
        """Replace a hashtag in the description with another one"""
        if not old_hashtag.startswith('#'):
            old_hashtag = f"#{old_hashtag}"
        if not new_hashtag.startswith('#'):
            new_hashtag = f"#{new_hashtag}"
        
        if self.description and old_hashtag in self.description:
            new_desc = self.description.replace(old_hashtag, new_hashtag)
            self.update_description_with_tags(new_desc)
    
    def has_hashtag(self, hashtag):
        """Check if post has a specific hashtag"""
        if not hashtag.startswith('#'):
            hashtag = f"#{hashtag}"
        return hashtag in (self.description or "")
    
    def get_content_preview(self):
        """Get a preview of the post content based on type"""
        if self.post_type == 'single_photo':
            return f"Photo: {self.content_object.title if self.content_object.title else 'Untitled'}"
        elif self.post_type == 'multiple_photos':
            photo_count = self.photos.count()
            return f"{photo_count} photos"
        elif self.post_type == 'collection':
            return f"Collection: {self.content_object.name}"
        return "Post"
    
    def increment_views(self, user=None, request=None):
        """Increment view count with unique tracking"""
        try:
            # Get session key and IP address
            session_key = None
            ip_address = None
            user_agent = ""
            
            if request:
                # Ensure session exists
                if not request.session.session_key:
                    request.session.create()
                
                session_key = request.session.session_key
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # For anonymous users, use a more strict tracking
            if not user:
                # Check for recent views from same IP + User-Agent (within last 30 minutes)
                from django.utils import timezone
                from datetime import timedelta
                
                recent_cutoff = timezone.now() - timedelta(minutes=30)
                
                recent_view = PostView.objects.filter(
                    post=self,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    viewed_at__gte=recent_cutoff
                ).first()
                
                if recent_view:
                    # Recent view exists, don't count this one
                    return
                
                # Also check for any view from same IP in last 5 minutes (anti-spam)
                spam_cutoff = timezone.now() - timedelta(minutes=5)
                spam_check = PostView.objects.filter(
                    post=self,
                    ip_address=ip_address,
                    viewed_at__gte=spam_cutoff
                ).count()
                
                if spam_check >= 3:  # Max 3 views per IP per 5 minutes
                    return
            
            # Check if we already have a view record for this identifier
            existing_view = PostView.objects.filter(
                post=self,
                session_key=session_key,
                ip_address=ip_address
            ).first()
            
            if not existing_view:
                # Create new view record
                PostView.objects.create(
                    post=self,
                    user=user,
                    session_key=session_key,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Update the cached view count
                self.views_count = self.view_records.count()
                self.save(update_fields=['views_count'])
                
            else:
                # View already exists, but let's check if it's old enough to count again
                from django.utils import timezone
                from datetime import timedelta
                
                # For authenticated users: 24 hours
                # For anonymous users: 2 hours (more strict)
                time_threshold = timedelta(hours=2) if not user else timedelta(hours=24)
                
                if existing_view.viewed_at < timezone.now() - time_threshold:
                    # Update existing view timestamp
                    existing_view.viewed_at = timezone.now()
                    existing_view.save(update_fields=['viewed_at'])
                    
                    # Increment view count
                    self.views_count += 1
                    self.save(update_fields=['views_count'])
                    
        except Exception as e:
            # If anything goes wrong, fallback to simple increment
            print(f"Error in view tracking, falling back to simple increment: {e}")
            self.views_count += 1
            self.save(update_fields=['views_count'])
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_unique_views_count(self):
        """Get the actual unique views count"""
        return self.view_records.count()
    
    def get_views_by_period(self, days=30):
        """Get views count for a specific period"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.view_records.filter(viewed_at__gte=cutoff_date).count()
    
    def reset_views_count(self):
        """Reset views count to match actual records (useful for data consistency)"""
        actual_count = self.view_records.count()
        if self.views_count != actual_count:
            self.views_count = actual_count
            self.save(update_fields=['views_count'])
        return self.views_count
    
    def force_increment_views(self):
        """Force increment views count (for testing or manual updates)"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
        return self.views_count
    
    @classmethod
    def cleanup_old_views(cls, days_to_keep=90):
        """Clean up old view records to keep database optimized"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        deleted_count, _ = PostView.objects.filter(viewed_at__lt=cutoff_date).delete()
        
        # Update all posts' view counts to match actual records
        for post in Post.objects.all():
            post.reset_views_count()
        
        return deleted_count
    
    def get_cover_image_url(self):
        """Get the cover image URL for the post"""
        if self.post_type == 'single_photo':
            return self.content_object.original_file.url
        elif self.post_type == 'multiple_photos':
            first_photo = self.photos.first()
            if first_photo:
                return first_photo.original_file.url
        elif self.post_type == 'collection':
            return self.content_object.get_cover_photo_url()
        return None



class PostLike(models.Model):
    """Model for post likes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "post"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} liked {self.post}"

class PostSave(models.Model):
    """Model for post saves (bookmarks)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post}"

class PostComment(models.Model):
    """Model for post comments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} on {self.post}: {self.content[:50]}..."


class PostView(models.Model):
    """Model for tracking unique post views"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='view_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_views', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('post', 'session_key', 'ip_address'),  # One view per session per IP per post
        ]
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['session_key', 'ip_address']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} viewed {self.post} at {self.viewed_at}"
        return f"Anonymous user viewed {self.post} at {self.viewed_at}"