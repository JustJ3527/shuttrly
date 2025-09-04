"""
URLs for photo similarity testing system.

This module provides URLs for testing the photo similarity system
including FAISS performance, different similarity methods, and
comparison tools.
"""

from django.urls import path
from . import test_views

# No app_name - we'll use the parent photos namespace

urlpatterns = [
    # Advanced similarity test with FAISS
    path("advanced/", test_views.test_advanced_similarity_view, name="test_advanced"),
    path("advanced/<int:photo_id>/", test_views.test_advanced_similarity_view, name="test_advanced_photo"),
    
    # Legacy test views (for backward compatibility)
    path("embedding/", test_views.test_embedding_system, name="test_embedding"),
    path("embedding/<int:photo_id>/", test_views.test_embedding_system, name="test_embedding_photo"),
    path("hybrid/", test_views.test_hybrid_system, name="test_hybrid"),
    path("hybrid/<int:photo_id>/", test_views.test_hybrid_system, name="test_hybrid_photo"),
]
