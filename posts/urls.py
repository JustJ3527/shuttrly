"""
URL patterns for the posts app
"""

from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # === POST LISTING ===
    path('', views.PostListView.as_view(), name='post_list'),
    path('feed/', views.user_feed_view, name='user_feed'),
    path('search/', views.post_search_view, name='post_search'),
    
    # === POST DETAILS ===
    path('<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    
    # === POST CREATION ===
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path('create/photo/', views.PostCreateView.as_view(), {'type': 'single_photo'}, name='create_photo_post'),
    path('create/photos/', views.PostCreateView.as_view(), {'type': 'multiple_photos'}, name='create_multiple_photos_post'),
    path('create/collection/', views.PostCreateView.as_view(), {'type': 'collection'}, name='create_collection_post'),
    
    # === POST EDITING ===
    path('<int:pk>/edit/', views.PostEditView.as_view(), name='post_edit'),
    path('<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    
    # === USER PROFILE POSTS ===
    path('user/<str:username>/', views.UserProfilePostsView.as_view(), name='user_profile_posts'),
    
    # === HASHTAG POSTS ===
    path('hashtag/<str:hashtag>/', views.hashtag_posts_view, name='hashtag_posts'),
    
    # === POST ENGAGEMENT ===
    path('<int:post_id>/like/', views.toggle_like_view, name='toggle_like'),
    path('<int:post_id>/save/', views.toggle_save_view, name='toggle_save'),
    path('<int:post_id>/comment/', views.add_comment_view, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment_view, name='delete_comment'),
    
    # === POST BULK ACTIONS ===
    path('bulk-action/', views.post_bulk_action_view, name='bulk_action'),
    
    # === AJAX ENDPOINTS ===
    path('<int:post_id>/stats/ajax/', views.ajax_post_stats_view, name='ajax_post_stats'),
    path('trending-hashtags/ajax/', views.ajax_trending_hashtags_view, name='ajax_trending_hashtags'),
    
    # === ERROR HANDLING ===
    path('404/', views.post_not_found_view, name='post_404'),
    path('403/', views.post_permission_denied_view, name='post_403'),
]