from django.urls import path
from . import views

app_name = "photos"

urlpatterns = [
    # Photo upload
    path("upload/", views.photo_upload, name="upload"),
    # Photo gallery and management
    path("gallery/", views.photo_gallery, name="gallery"),
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
]
