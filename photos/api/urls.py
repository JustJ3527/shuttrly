from django.urls import path
from . import views

app_name = "photos_api"

urlpatterns = [
    # Photos endpoints
    path("photos/", views.PhotoListAPIView.as_view(), name="photo-list"),
    path("photos/all/", views.PhotoListAllAPIView.as_view(), name="photo-list-all"),  # Nouvel endpoint
    path("photos/<int:pk>/", views.PhotoDetailAPIView.as_view(), name="photo-detail"),
    path("photos/<int:pk>/full/", views.PhotoDetailFullAPIView.as_view(), name="photo-detail-full"),  # Nouvel endpoint complet
    path("photos/upload/", views.PhotoUploadAPIView.as_view(), name="photo-upload"),
    path("photos/<int:pk>/delete/", views.PhotoDeleteAPIView.as_view(), name="photo-delete"),
    
    # Collections endpoints
    path("collections/", views.CollectionListAPIView.as_view(), name="collection-list"),
    path("collections/<int:pk>/", views.CollectionDetailAPIView.as_view(), name="collection-detail"),
    path("collections/<int:pk>/photos/", views.CollectionPhotosAPIView.as_view(), name="collection-photos"),
    
    # Gallery endpoints
    path("gallery/", views.GalleryAPIView.as_view(), name="gallery"),
    path("gallery/user/<int:user_id>/", views.UserGalleryAPIView.as_view(), name="user-gallery"),
    path("gallery/public/", views.PublicGalleryAPIView.as_view(), name="public-gallery"),
    
    # Search and filter endpoints
    path("photos/search/", views.PhotoSearchAPIView.as_view(), name="photo-search"),
    path("photos/tags/", views.TagListAPIView.as_view(), name="tag-list"),
    path("photos/tags/<str:tag_name>/", views.PhotosByTagAPIView.as_view(), name="photos-by-tag"),
    
    # Stats endpoints
    path("stats/", views.PhotoStatsAPIView.as_view(), name="photo-stats"),
    path("stats/user/<int:user_id>/", views.UserPhotoStatsAPIView.as_view(), name="user-photo-stats"),
]
