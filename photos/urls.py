from django.urls import path, include
from . import views

app_name = "photos"

urlpatterns = [
    # API endpoints
    path("api/", include("photos.api.urls")),
    # Photo upload
    path("upload/", views.photo_upload, name="upload"),
    # Photo gallery and management
    path("gallery/", views.photo_gallery, name="gallery"),
    path("gallery-advanced/", views.advanced_gallery, name="advanced_gallery"),
    path("gallery-test/", views.photo_gallery_test, name="gallery_test"),
    path("stats/", views.photo_stats, name="stats"),
    # Individual photo views
    path("photo/<int:photo_id>/", views.photo_detail, name="detail"),
    path("photo/<int:photo_id>/edit/", views.photo_edit, name="edit"),
    path("photo/<int:photo_id>/delete/", views.photo_delete, name="delete"),
    path("photo/<int:photo_id>/download/", views.download_photo, name="download"),
    # Public gallery
    path("public/", views.public_gallery, name="public_gallery"),
    # Bulk actions
    path("bulk-actions/", views.bulk_actions, name="bulk_actions"),
    path("add-to-collection/", views.add_to_collection, name="add_to_collection"),
    path("advanced-bulk-actions/", views.advanced_bulk_actions, name="advanced_bulk_actions"),
    # AJAX endpoints
    path(
        "ajax/upload-progress/", views.ajax_upload_progress, name="ajax_upload_progress"
    ),
    # Progress tracking
    path("upload-progress/", views.get_upload_progress, name="upload_progress"),
    path(
        "clear-upload-progress/",
        views.clear_upload_progress,
        name="clear_upload_progress",
    ),
    # Collections
    path("collections/", views.collection_list, name="collection_list"),
    path("collections/create/", views.collection_create, name="collection_create"),
    path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("collections/<int:collection_id>/edit/", views.collection_edit, name="collection_edit"),
    path("collections/<int:collection_id>/delete/", views.collection_delete, name="collection_delete"),
    path("collections/<int:collection_id>/add-photos/", views.collection_add_photos, name="collection_add_photos"),
    path("collections/<int:collection_id>/remove-photo/<int:photo_id>/", views.collection_remove_photo, name="collection_remove_photo"),
    path("collections/<int:collection_id>/reorder/", views.collection_reorder_photos, name="collection_reorder_photos"),
    # Tags
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/<str:tag_name>/", views.tag_detail, name="tag_detail"),
    path("tags/search/", views.search_by_tags, name="search_by_tags"),
    # Legacy embedding system test (moved to test module)
    # path("test-embedding/", views.test_embedding_system, name="test_embedding"),
    # path("test-embedding/<int:photo_id>/", views.test_embedding_system, name="test_embedding_photo"),
    # path("test-hybrid/", views.test_hybrid_system, name="test_hybrid"),
    # path("test-hybrid/<int:photo_id>/", views.test_hybrid_system, name="test_hybrid_photo"),
    # Test system (separate module)
    path("test/", include("photos.test.urls")),
]
