from django.contrib import admin
from .models import Post, PostLike, PostSave, PostComment, PostView

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'post_type', 'title', 'visibility', 'likes_count', 'comments_count', 'views_count', 'created_at']
    list_filter = ['post_type', 'visibility', 'is_featured', 'created_at', 'author']
    search_fields = ['title', 'description', 'author__username', 'tags']
    readonly_fields = ['likes_count', 'comments_count', 'views_count', 'shares_count', 'saves_count', 'created_at', 'updated_at', 'published_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('author', 'title', 'description', 'tags', 'post_type')
        }),
        ('Content', {
            'fields': ('content_type', 'object_id', 'photos', 'visibility')
        }),
        ('Engagement', {
            'fields': ('is_featured', 'likes_count', 'comments_count', 'views_count', 'shares_count', 'saves_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title']
    date_hierarchy = 'created_at'

@admin.register(PostSave)
class PostSaveAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title']
    date_hierarchy = 'created_at'

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'parent_comment', 'content', 'created_at']
    list_filter = ['created_at', 'parent_comment']
    search_fields = ['user__username', 'post__title', 'content']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'ip_address', 'session_key', 'viewed_at']
    list_filter = ['viewed_at', 'post__post_type']
    search_fields = ['post__title', 'user__username', 'ip_address']
    date_hierarchy = 'viewed_at'
    readonly_fields = ['viewed_at']
    
    fieldsets = (
        ('View Information', {
            'fields': ('post', 'user', 'viewed_at')
        }),
        ('Technical Details', {
            'fields': ('session_key', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
