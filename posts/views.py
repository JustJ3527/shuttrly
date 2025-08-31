"""
Views for the posts app
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from django.core.exceptions import ValidationError

from .models import Post, PostLike, PostSave, PostComment
from .forms import (
    PostCreateForm,
    PostEditForm,
    PostCommentForm,
    PostSearchForm,
    PostBulkActionForm,
)
from .utils import (
    toggle_post_like,
    toggle_post_save,
    delete_post_comment,
    get_user_feed_posts,
    get_posts_by_hashtag,
    get_trending_hashtags,
    get_post_statistics,
    get_user_post_stats,
)
from photos.models import Photo, Collection
from users.models import CustomUser


# === POST LISTING VIEWS ===

class PostListView(ListView):
    """Display a list of posts with filtering and search"""
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 12  # Reduced for better performance
    
    def get_queryset(self):
        """Get filtered queryset based on request parameters"""
        queryset = Post.objects.select_related(
            'author', 'content_type'
        ).prefetch_related(
            'photos', 
            'comments__user',
            'likes',
            'saves'
        ).filter(visibility='public')
        
        # Apply search filters
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(description__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        # Apply hashtag filter
        hashtags = self.request.GET.get('hashtags', '')
        if hashtags:
            hashtag_list = [tag.strip() for tag in hashtags.split(',') if tag.strip()]
            for hashtag in hashtag_list:
                if hashtag.startswith('#'):
                    queryset = queryset.filter(tags__icontains=hashtag)
        
        # Apply sorting
        sort_by = self.request.GET.get('sort', 'recent')
        if sort_by == 'popular':
            queryset = queryset.order_by('-likes_count', '-published_at')
        elif sort_by == 'trending':
            queryset = queryset.annotate(
                engagement_score=F('likes_count') + F('comments_count') + F('views_count')
            ).order_by('-engagement_score', '-published_at')
        else:  # recent
            queryset = queryset.order_by('-published_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        context['trending_hashtags'] = get_trending_hashtags(limit=10)
        context['search_form'] = PostSearchForm(self.request.GET)
        
        # Add pagination info for infinite scroll
        paginator = context['paginator']
        page_obj = context['page_obj']
        
        context['has_next'] = page_obj.has_next()
        context['has_previous'] = page_obj.has_previous()
        context['total_pages'] = paginator.num_pages
        context['current_page'] = page_obj.number
        
        return context
    
    def get_template_names(self):
        """Return appropriate template based on request type"""
        # Check if this is an AJAX request for infinite scroll
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ["posts/partials/_post_list.html"]
        return [self.template_name]


class UserProfilePostsView(ListView):
    """Display posts from a specific user's profile"""
    model = Post
    template_name = "posts/user_profile_posts.html"
    context_object_name = "posts"
    paginate_by = 15
    
    def get_queryset(self):
        """Get posts for the specified user"""
        username = self.kwargs.get('username')
        user = get_object_or_404(CustomUser, username=username)
        
        # Check if current user can see private posts
        if self.request.user == user:
            queryset = Post.objects.filter(author=user)
        else:
            queryset = Post.objects.filter(
                author=user,
                visibility__in=['public', 'friends']
            )
        
        return queryset.select_related('author', 'content_type').prefetch_related('photos')
    
    def get_context_data(self, **kwargs):
        """Add user profile data to context"""
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        user = get_object_or_404(CustomUser, username=username)
        context['profile_user'] = user
        context['user_stats'] = get_user_post_stats(user)
        return context


# === POST DETAIL VIEWS ===

class PostDetailView(DetailView):
    """Display a single post with comments and engagement options"""
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"
    
    def get_queryset(self):
        """Get post with related data"""
        return Post.objects.select_related(
            'author', 'content_type'
        ).prefetch_related('photos', 'comments', 'comments__user')
    
    def get_object(self, queryset=None):
        """Get post and check visibility permissions"""
        post = super().get_object(queryset)
        
        # Check visibility permissions
        if post.visibility == 'private' and self.request.user != post.author:
            raise Http404("Post not found")
        elif post.visibility == 'friends' and self.request.user != post.author:
            # Check if users are friends (implement your friendship logic here)
            if not self.request.user.is_authenticated:
                raise Http404("Post not found")
            # Add friendship check logic here
        
        return post
    
    def dispatch(self, request, *args, **kwargs):
        """Handle view counting in dispatch to avoid multiple calls"""
        response = super().dispatch(request, *args, **kwargs)
        
        # Only increment views for GET requests (not POST, etc.)
        if request.method == 'GET':
            post = self.get_object()
            # Increment view count with unique tracking
            post.increment_views(user=request.user, request=request)
        
        return response
    
    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Add comment form
        context['comment_form'] = PostCommentForm(
            user=self.request.user,
            post=post
        )
        
        # Add engagement status for current user
        if self.request.user.is_authenticated:
            context['user_liked'] = PostLike.objects.filter(
                user=self.request.user, post=post
            ).exists()
            context['user_saved'] = PostSave.objects.filter(
                user=self.request.user, post=post
            ).exists()
        
        # Add post statistics
        context['post_stats'] = get_post_statistics(post)
        
        return context


# === POST CREATION VIEWS ===

class PostCreateView(LoginRequiredMixin, CreateView):
    """Create a new post"""
    model = Post
    template_name = "posts/post_create.html"
    form_class = PostCreateForm
    success_url = reverse_lazy('posts:post_list')
    
    def get_form_kwargs(self):
        """Pass user and post type to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['post_type'] = self.request.GET.get('type', 'single_photo')
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add context for post creation"""
        context = super().get_context_data(**kwargs)
        post_type = self.request.GET.get('type', 'single_photo')
        
        if post_type == 'single_photo':
            context['photos'] = Photo.objects.filter(user=self.request.user).order_by('-created_at')
        elif post_type == 'multiple_photos':
            context['photos'] = Photo.objects.filter(user=self.request.user).order_by('-created_at')
        elif post_type == 'collection':
            context['collections'] = Collection.objects.filter(owner=self.request.user).order_by('-created_at')
        
        context['post_type'] = post_type
        return context
    
    def get_template_names(self):
        """Return appropriate template based on request type"""
        # Check if this is an HTMX request
        if self.request.headers.get('HX-Request'):
            return ["posts/partials/post_content.html"]
        return [self.template_name]
    
    def form_valid(self, form):
        """Handle form validation and post creation"""
        try:
            post = form.save()
            messages.success(self.request, f"Post created successfully!")
            return redirect('posts:post_detail', pk=post.pk)
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


# === POST EDITING VIEWS ===

class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an existing post"""
    model = Post
    template_name = "posts/post_edit.html"
    form_class = PostEditForm
    success_url = reverse_lazy('posts:post_list')
    
    def test_func(self):
        """Check if user can edit this post"""
        post = self.get_object()
        return self.request.user == post.author
    
    def get_form_kwargs(self):
        """Pass user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """Handle form validation"""
        post = form.save()
        messages.success(self.request, "Post updated successfully!")
        return redirect('posts:post_detail', pk=post.pk)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a post"""
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy('posts:post_list')
    
    def test_func(self):
        """Check if user can delete this post"""
        post = self.get_object()
        return self.request.user == post.author
    
    def delete(self, request, *args, **kwargs):
        """Handle post deletion"""
        post = self.get_object()
        messages.success(request, "Post deleted successfully!")
        return super().delete(request, *args, **kwargs)


# === POST FEED VIEWS ===

@login_required
def user_feed_view(request):
    """Display personalized feed for the current user"""
    page = request.GET.get('page', 1)
    
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    feed_data = get_user_feed_posts(request.user, page=page, per_page=12)  # Reduced for better performance
    
    # Get user's liked and saved posts for current page
    current_posts = feed_data['posts']
    user_liked_posts = set(PostLike.objects.filter(
        user=request.user, 
        post__in=current_posts
    ).values_list('post_id', flat=True))
    
    user_saved_posts = set(PostSave.objects.filter(
        user=request.user, 
        post__in=current_posts
    ).values_list('post_id', flat=True))
    
    context = {
        'posts': feed_data['posts'],
        'has_next': feed_data['has_next'],
        'has_previous': feed_data['has_previous'],
        'total_pages': feed_data['total_pages'],
        'current_page': page,
        'trending_hashtags': get_trending_hashtags(limit=10),
        'user_posts_count': Post.objects.filter(author=request.user).count(),
        'user_likes_count': PostLike.objects.filter(user=request.user).count(),
        'user_comments_count': PostComment.objects.filter(user=request.user).count(),
        'user_saves_count': PostSave.objects.filter(user=request.user).count(),
        'user_liked_posts': user_liked_posts,
        'user_saved_posts': user_saved_posts,
        'user': request.user,  # Add user to context for template comparison
    }
    
    # Check if this is an AJAX request for infinite scroll
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'posts/partials/_user_feed_posts.html', context)
    
    return render(request, 'posts/user_feed.html', context)


# === HASHTAG VIEWS ===

def hashtag_posts_view(request, hashtag):
    """Display posts with a specific hashtag"""
    # Remove # if present
    clean_hashtag = hashtag.lstrip('#')
    
    posts = get_posts_by_hashtag(f"#{clean_hashtag}", user=request.user)
    
    # Paginate results
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'hashtag': clean_hashtag,
        'posts': page_obj,
        'posts_count': posts.count(),
        'trending_hashtags': get_trending_hashtags(limit=10)
    }
    
    return render(request, 'posts/hashtag_posts.html', context)


# === POST ENGAGEMENT VIEWS ===

@login_required
@require_POST
def toggle_like_view(request, post_id):
    """Toggle like status for a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        result = toggle_post_like(request.user, post)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)
        else:
            messages.success(request, result['message'])
            return redirect('posts:post_detail', pk=post_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        else:
            messages.error(request, f"Error: {str(e)}")
            return redirect('posts:post_detail', pk=post_id)


@login_required
@require_POST
def toggle_save_view(request, post_id):
    """Toggle save status for a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        result = toggle_post_save(request.user, post)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)
        else:
            messages.success(request, result['message'])
            return redirect('posts:post_detail', pk=post_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        else:
            messages.error(request, f"Error: {str(e)}")
            return redirect('posts:post_detail', pk=post_id)


@login_required
@require_POST
def add_comment_view(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        form = PostCommentForm(
            user=request.user,
            post=post,
            data=request.POST
        )
        
        if form.is_valid():
            comment = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Comment added successfully!',
                    'comment': {
                        'id': comment.id,
                        'content': comment.content,
                        'user': comment.user.username,
                        'created_at': comment.created_at.isoformat(),
                    }
                })
            else:
                messages.success(request, "Comment added successfully!")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Error adding comment. Please check your input.',
                    'errors': form.errors
                }, status=400)
            else:
                messages.error(request, "Error adding comment. Please check your input.")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    return redirect('posts:post_detail', pk=post_id)


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(PostComment, id=comment_id)
    
    if comment.user != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You can only delete your own comments.'
            }, status=403)
        else:
            messages.error(request, "You can only delete your own comments.")
            return redirect('posts:post_detail', pk=comment.post.pk)
    
    result = delete_post_comment(request.user, comment)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(result)
    else:
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
        return redirect('posts:post_detail', pk=comment.post.pk)


# === POST SEARCH AND FILTERING ===

def post_search_view(request):
    """Search and filter posts"""
    form = PostSearchForm(request.GET)
    posts = Post.objects.none()
    
    if form.is_valid():
        cleaned_data = form.cleaned_data
        
        # Build base queryset
        posts = Post.objects.select_related('author', 'content_type').prefetch_related('photos')
        
        # Apply search filters
        if cleaned_data.get('query'):
            query = cleaned_data['query']
            posts = posts.filter(
                Q(description__icontains=query) |
                Q(title__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Apply type filter
        if cleaned_data.get('search_type') == 'photos':
            posts = posts.filter(post_type__in=['single_photo', 'multiple_photos'])
        elif cleaned_data.get('search_type') == 'collections':
            posts = posts.filter(post_type='collection')
        elif cleaned_data.get('search_type') == 'my_posts':
            if request.user.is_authenticated:
                posts = posts.filter(author=request.user)
            else:
                posts = Post.objects.none()
        
        # Apply hashtag filter
        if cleaned_data.get('hashtags'):
            hashtags = cleaned_data['hashtags']
            hashtag_list = [tag.strip() for tag in hashtags.split(',') if tag.strip()]
            for hashtag in hashtag_list:
                if hashtag.startswith('#'):
                    posts = posts.filter(tags__icontains=hashtag)
        
        # Apply date filters
        if cleaned_data.get('date_from'):
            posts = posts.filter(published_at__gte=cleaned_data['date_from'])
        if cleaned_data.get('date_to'):
            posts = posts.filter(published_at__lte=cleaned_data['date_to'])
        
        # Apply sorting
        sort_by = cleaned_data.get('sort_by', 'recent')
        if sort_by == 'popular':
            posts = posts.order_by('-likes_count', '-published_at')
        elif sort_by == 'trending':
            posts = posts.annotate(
                engagement_score=F('likes_count') + F('comments_count') + F('views_count')
            ).order_by('-engagement_score', '-published_at')
        elif sort_by == 'likes':
            posts = posts.order_by('-likes_count', '-published_at')
        elif sort_by == 'views':
            posts = posts.order_by('-views_count', '-published_at')
        else:  # recent
            posts = posts.order_by('-published_at')
        
        # Filter by visibility
        if request.user.is_authenticated:
            posts = posts.filter(
                Q(visibility='public') |
                Q(author=request.user) |
                Q(visibility='friends', author__in=request.user.friends.all())
            )
        else:
            posts = posts.filter(visibility='public')
    
    # Paginate results
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'posts': page_obj,
        'trending_hashtags': get_trending_hashtags(limit=10)
    }
    
    return render(request, 'posts/post_search.html', context)


# === POST BULK ACTIONS ===

@login_required
@require_POST
def post_bulk_action_view(request):
    """Handle bulk actions on posts"""
    form = PostBulkActionForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        post_ids = form.cleaned_data['post_ids'].split(',')
        
        # Get posts that user can modify
        posts = Post.objects.filter(
            id__in=post_ids,
            author=request.user
        )
        
        if action == 'delete':
            count = posts.count()
            posts.delete()
            messages.success(request, f"{count} posts deleted successfully!")
            
        elif action == 'change_visibility':
            new_visibility = form.cleaned_data['new_visibility']
            count = posts.update(visibility=new_visibility)
            messages.success(request, f"Visibility updated for {count} posts!")
            
        elif action == 'add_hashtags':
            hashtags_to_add = form.cleaned_data['hashtags_to_add']
            count = 0
            for post in posts:
                for hashtag in hashtags_to_add.split():
                    if hashtag.strip():
                        post.add_hashtag_to_description(hashtag.strip())
                        count += 1
            messages.success(request, f"Added {count} hashtags to posts!")
            
        elif action == 'remove_hashtags':
            hashtags_to_remove = form.cleaned_data['hashtags_to_remove']
            count = 0
            for post in posts:
                for hashtag in hashtags_to_remove.split():
                    if hashtag.strip():
                        post.remove_hashtag_from_description(hashtag.strip())
                        count += 1
            messages.success(request, f"Removed {count} hashtags from posts!")
            
        elif action == 'feature':
            count = posts.update(is_featured=True)
            messages.success(request, f"{count} posts featured!")
            
        elif action == 'unfeature':
            count = posts.update(is_featured=False)
            messages.success(request, f"{count} posts unfeatured!")
    
    return redirect('posts:post_list')


# === AJAX VIEWS ===

@login_required
@require_POST
@csrf_exempt
def ajax_post_stats_view(request, post_id):
    """Get post statistics via AJAX"""
    try:
        post = get_object_or_404(Post, id=post_id)
        stats = get_post_statistics(post)
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def ajax_trending_hashtags_view(request):
    """Get trending hashtags via AJAX"""
    try:
        limit = int(request.POST.get('limit', 10))
        hashtags = get_trending_hashtags(limit=limit)
        return JsonResponse({'hashtags': hashtags})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# === ERROR HANDLING ===

def post_not_found_view(request, exception=None):
    """Handle 404 errors for posts"""
    return render(request, 'posts/404.html', status=404)


def post_permission_denied_view(request, exception=None):
    """Handle 403 errors for posts"""
    return render(request, 'posts/403.html', status=403)