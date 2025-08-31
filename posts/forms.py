"""
Forms for the posts app
"""
# Django imports
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

# Local imports
from .models import Post, PostComment
from photos.models import Photo, Collection
from .utils import validate_hashtag, suggest_hashtags

User = get_user_model()

class PostCreateForm(forms.ModelForm):
    """Form for creating new posts"""
    
    # Custom fields for better UX
    photo_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Comma-separated photo IDs for multiple photos post"
    )
    collection_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Collection ID for collection post"
    )

    class Meta:
        model = Post
        fields = ["title", "description", "visibility"]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your post a title (optional)',
                'maxlength': '200'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Describe your post... Use #hashtags for better discoverability!',
                'style': 'resize: vertical;'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        
    def __init__(self, *args, **kwargs):
        """Initialize the form"""
        self.user = kwargs.pop("user", None)
        self.post_type = kwargs.pop("post_type", None)
        super().__init__(*args, **kwargs)
        
        # Set initial visibility based on user preferences
        if self.user and hasattr(self.user, "is_private"):
            self.fields["visibility"].initial = "private" if self.user.is_private else "public"

        # Add hashtag suggestions
        self.fields["description"].help_text += self._get_hashtag_suggestions()

    def _get_hashtag_suggestions(self):
        """Get hashtag suggestions based on user's photos/collections"""
        if not self.user:
            return ""
        
        suggestions = []
        
        # Get hashtags from user's recent photos
        recent_photos = Photo.objects.filter(user=self.user).order_by("-created_at")[:5]
        for photo in recent_photos:
            if photo.tags:
                suggestions.extend(photo.get_tags_list()[:3])
            
        # Get hashtags from user's collections
        recent_collections = Collection.objects.filter(owner=self.user).order_by('-created_at')[:3]
        for collection in recent_collections:
            if collection.tags:
                suggestions.extend(collection.get_tags_list()[:2])

        # Remove duplicates and limit to 5
        unique_suggestions = list(dict.fromkeys(suggestions))[:5]

        if unique_suggestions:
            return f"💡 Suggested hashtags: {", ".join([f"#{tag}"for tag in unique_suggestions])}"
        return ""

    def clean_description(self):
        """Clean and validate the description"""
        description = self.cleaned_data.get("description", "")

        # Strip HTML tags
        description = strip_tags(description)

        # Validate hashtag syntax
        hashtags = self._extract_hashtags(description)
        invalid_hashtags = []

        for hashtag in hashtags:
            if not validate_hashtag(hashtag):
                invalid_hashtags.append(hashtag)

        if invalid_hashtags:
            raise ValidationError(
                f"Invalid hashtags: {", ".join(invalid_hashtags)}. "
                "Hashtags must start with # and contain only letters and numbers."
            )

        return description

    def clean(self):
        """Clean and validate form data"""
        cleaned_data = super().clean()
        post_type = self.post_type or cleaned_data.get("post_type")

        if not post_type:
            raise ValidationError("Post type is required")

        # Validate based on post type
        if post_type == "single_photo":
            if not cleaned_data.get('photo_ids'):
                raise ValidationError("Please select a photo for this post")
        elif post_type == 'multiple_photos':
            if not cleaned_data.get('photo_ids'):
                raise ValidationError("Please select at least one photo for this post")
        elif post_type == 'collection':
            if not cleaned_data.get('collection_id'):
                raise ValidationError("Please select a collection for this post")

        return cleaned_data

    def _extract_hashtags(self, text):
        """Extract hashtags from text"""
        import re
        hashtags = re.findall(r"#(\w+)", text)
        return hashtags
    
    def save(self, commit=True):
        """Save the post with proper content object"""
        post = super().save(commit=False)
        post.author = self.user
        post.post_type = self.post_type

        # Set content object based on post type
        if self.post_type == "single_photo":
            photo_id = self.cleaned_data.get("photo_ids")
            if photo_id:
                try:
                    photo = Photo.objects.get(id=photo_id, user=self.user)
                    post.content_type = ContentType.objects.get_for_model(Photo)
                    post.object_id = photo.id
                except Photo.DoesNotExist:
                    raise ValidationError("Selected photo not found")

        elif self.post_type == "multiple_photos":
            photo_ids = self.cleaned_data.get("photo_ids")
            if photo_ids:
                photo_id_list = [pid.strip() for pid in photo_ids.split(",") if pid.strip()]
                photos = Photo.objects.filter(id__in=photo_id_list, user=self.user)

                if photos.exists():
                    # Use first photo as content object
                    first_photo = photos.first()
                    post.content_type = ContentType.objects.get_for_model(Photo)
                    post.object_id = first_photo.id

                    if commit:
                        post.save()
                        post.photos.set(photos)
                        return post
                else:
                    raise ValidationError("Some selected photos were not found")

        elif self.post_type == "collection":
            collection_id = self.cleaned_data.get('collection_id')
            if collection_id:
                try:
                    collection = Collection.objects.get(id=collection_id, owner=self.user)
                    post.content_type = ContentType.objects.get_for_model(Collection)
                    post.object_id = collection.id
                except Collection.DoesNotExist:
                    raise ValidationError("Selected collection not found")
        
        if commit:
            post.save()
        return post


class PostEditForm(forms.ModelForm):
    """Form for editing existing posts"""

    class Meta:
        model = Post
        fields = ["title", "description", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs= {
                "class": "form-control",
                "placeholder": "Give your post a title (optional)",
                "maxlength": "200"
            }),
            "description": forms.Textarea(attrs= {
                "class": "form-control",
                "rows": "4",
                "placeholder": "Describe your post... Use #hashtags for better discoverability!",
                "style": "resize: vertical;"
            }),
            "visibility": forms.Select(attrs= {
                "class": "form-select"
            })
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form"""
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Add hashtag suggestions based on current content
        if self.instance and self.instance.description:
            suggestions = suggest_hashtags(self.instance.description, limit=5)
            if suggestions:
                self.fields["description"].help_text += f" 💡 Current hashtags: {', '.join(suggestions)}"
        
    def clean_description(self):
        """Clean and validate the description"""
        description = self.cleaned_data.get("description", "")

        # Strip HTML tags
        description = strip_tags(description)

        # Validate hashtag syntax
        hashtags = self._extract_hashtags(description)
        invalid_hashtags = []

        for hashtag in hashtags:
            if not validate_hashtag(hashtag):
                invalid_hashtags.append(hashtag)
        
        if invalid_hashtags:
            raise ValidationError(
                f"Invalid hashtags: {', '.join(invalid_hashtags)}. "
                "Hashtags must start with # and contain only letters and numbers."
            )

        return description
    
    def _extract_hashtags(self, text):
        """Extract hashtags from text"""
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags

    def save(self, commit=True):
        """Save the post with updated tags"""
        post = super().save(commit=False)
        
        # Tags will be automatically updated via the model's save method
        # when the description is saved
        
        if commit:
            post.save()
        return post


class PostCommentForm(forms.ModelForm):
    """Form for adding comments to posts"""
    
    class Meta:
        model = PostComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Write a comment...',
                'style': 'resize: vertical;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.post = kwargs.pop('post', None)
        self.parent_comment = kwargs.pop('parent_comment', None)
        super().__init__(*args, **kwargs)
        
        if self.parent_comment:
            self.fields['content'].widget.attrs['placeholder'] = f'Reply to {self.parent_comment.user.username}...'
    
    def clean_content(self):
        """Clean and validate comment content"""
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise ValidationError("Comment cannot be empty")
        
        if len(content) > 1000:
            raise ValidationError("Comment is too long (maximum 1000 characters)")
        
        # Strip HTML tags
        content = strip_tags(content)
        
        return content
    
    def save(self, commit=True):
        """Save the comment with proper relationships"""
        comment = super().save(commit=False)
        comment.user = self.user
        comment.post = self.post
        
        if self.parent_comment:
            comment.parent_comment = self.parent_comment
        
        if commit:
            comment.save()
        return comment


class PostSearchForm(forms.Form):
    """Form for searching posts"""
    
    SEARCH_CHOICES = [
        ('all', 'All Posts'),
        ('photos', 'Photos Only'),
        ('collections', 'Collections Only'),
        ('my_posts', 'My Posts'),
        ('following', 'Following'),
    ]
    
    SORT_CHOICES = [
        ('recent', 'Most Recent'),
        ('popular', 'Most Popular'),
        ('trending', 'Trending'),
        ('likes', 'Most Liked'),
        ('views', 'Most Viewed'),
    ]
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search posts, hashtags, or descriptions...',
            'autocomplete': 'off'
        })
    )
    
    search_type = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        initial='recent',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    hashtags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by hashtags (e.g., #nature #city)',
            'autocomplete': 'off'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean_hashtags(self):
        """Clean and validate hashtags"""
        hashtags = self.cleaned_data.get('hashtags', '')
        
        if hashtags:
            # Extract hashtags and validate them
            import re
            found_hashtags = re.findall(r'#(\w+)', hashtags)
            
            invalid_hashtags = []
            for hashtag in found_hashtags:
                if not validate_hashtag(hashtag):
                    invalid_hashtags.append(hashtag)
            
            if invalid_hashtags:
                raise ValidationError(
                    f"Invalid hashtags: {', '.join(invalid_hashtags)}. "
                    "Hashtags must contain only letters, numbers, and underscores."
                )
        
        return hashtags


class PostBulkActionForm(forms.Form):
    """Form for bulk actions on posts"""
    
    ACTION_CHOICES = [
        ('delete', 'Delete Selected Posts'),
        ('change_visibility', 'Change Visibility'),
        ('add_hashtags', 'Add Hashtags'),
        ('remove_hashtags', 'Remove Hashtags'),
        ('feature', 'Feature Posts'),
        ('unfeature', 'Unfeature Posts'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends Only'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    post_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    new_visibility = forms.ChoiceField(
        choices=VISIBILITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    hashtags_to_add = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hashtags to add (e.g., #nature #city)'
        })
    )
    
    hashtags_to_remove = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hashtags to remove (e.g., #nature #city)'
        })
    )
    
    def clean(self):
        """Validate form data based on selected action"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if action == 'change_visibility' and not cleaned_data.get('new_visibility'):
            raise ValidationError("Please select a new visibility setting")
        
        elif action == 'add_hashtags' and not cleaned_data.get('hashtags_to_add'):
            raise ValidationError("Please specify hashtags to add")
        
        elif action == 'remove_hashtags' and not cleaned_data.get('hashtags_to_remove'):
            raise ValidationError("Please specify hashtags to remove")
        
        return cleaned_data