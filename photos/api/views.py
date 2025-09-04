from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from photos.models import Photo, Collection, CollectionPhoto
from .serializers import (
    PhotoSerializer, PhotoListSerializer, PhotoUploadSerializer,
    CollectionSerializer, CollectionPhotoSerializer, PhotoSearchSerializer
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PhotoListAPIView(generics.ListAPIView):
    """API endpoint for listing photos with pagination"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'title', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return photos for the authenticated user"""
        return Photo.objects.filter(user=self.request.user).select_related('user')
    
    def get_paginated_response(self, data):
        """Override to handle pagination toggle"""
        # Check if user wants all photos
        if self.request.query_params.get('all') == 'true':
            queryset = self.get_queryset()
            return Response({
                'count': queryset.count(),
                'total_photos': queryset.count(),
                'results': data,
                'message': 'Toutes les photos récupérées (pagination désactivée)',
                'pagination_disabled': True
            })
        
        # Return normal paginated response
        return super().get_paginated_response(data)
    
    def paginate_queryset(self, queryset):
        """Override to conditionally disable pagination"""
        # Check if user wants all photos
        if self.request.query_params.get('all') == 'true':
            return None  # Disable pagination
        
        # Return normal pagination
        return super().paginate_queryset(queryset)


class PhotoListAllAPIView(generics.ListAPIView):
    """API endpoint for listing ALL photos without pagination"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = None  # Pas de pagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'title', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return ALL photos for the authenticated user"""
        return Photo.objects.filter(user=self.request.user).select_related('user')
    
    def list(self, request, *args, **kwargs):
        """Override to return all photos in a single response"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'total_photos': queryset.count(),
            'results': serializer.data,
            'message': 'Toutes les photos récupérées sans pagination'
        })


class PhotoDetailAPIView(generics.RetrieveAPIView):
    """API endpoint for retrieving a single photo"""
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    queryset = Photo.objects.all()
    
    def get_queryset(self):
        """Return photos for the authenticated user"""
        return Photo.objects.filter(user=self.request.user).select_related('user')


class PhotoDetailFullAPIView(generics.RetrieveAPIView):
    """API endpoint for retrieving ALL detailed information about a single photo"""
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    queryset = Photo.objects.all()
    
    def get_queryset(self):
        """Return photos for the authenticated user"""
        return Photo.objects.filter(user=self.request.user).select_related('user')
    
    def retrieve(self, request, *args, **kwargs):
        """Override to return comprehensive photo information"""
        photo = self.get_object()
        
        # Get basic serializer data
        serializer = self.get_serializer(photo)
        data = serializer.data
        
        # Add comprehensive information
        comprehensive_data = {
            "photo_id": photo.id,
            "basic_info": {
                "title": photo.title,
                "description": photo.description,
                "tags": photo.tags,
                "tags_list": photo.get_tags_list(),
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
                "is_private": photo.is_private,
                "is_featured": photo.is_featured,
            },
            "file_info": {
                "file_size_bytes": photo.file_size,
                "file_size_mb": photo.get_file_size_mb(),
                "file_extension": photo.file_extension,
                "is_raw": photo.is_raw,
                "original_file_url": request.build_absolute_uri(photo.original_file.url) if photo.original_file else None,
                "thumbnail_url": request.build_absolute_uri(photo.thumbnail.url) if photo.thumbnail else None,
            },
            "dimensions": {
                "width": photo.width,
                "height": photo.height,
                "dimensions_display": photo.get_dimensions_display(),
                "aspect_ratio": round(photo.width / photo.height, 2) if photo.width and photo.height else None,
            },
            "camera_info": {
                "camera_make": photo.camera_make,
                "camera_model": photo.camera_model,
                "lens_make": photo.lens_make,
                "lens_model": photo.lens_model,
                "camera_display": photo.get_camera_display(),
            },
            "exposure_settings": {
                "focal_length": photo.focal_length,
                "focal_length_35mm": photo.focal_length_35mm,
                "shutter_speed": photo.shutter_speed,
                "aperture": photo.aperture,
                "iso": photo.iso,
                "exposure_bias": photo.exposure_bias,
                "exposure_mode": photo.exposure_mode,
                "metering_mode": photo.metering_mode,
                "exposure_display": photo.get_exposure_display(),
            },
            "image_settings": {
                "white_balance": photo.white_balance,
                "color_space": photo.color_space,
                "flash": photo.flash,
                "digital_zoom_ratio": photo.digital_zoom_ratio,
            },
            "location_data": {
                "latitude": photo.latitude,
                "longitude": photo.longitude,
                "altitude": photo.altitude,
                "location_description": photo.location_description,
                "has_gps": bool(photo.latitude and photo.longitude),
            },
            "time_data": {
                "date_taken": photo.date_taken,
                "date_modified": photo.date_modified,
                "created_at": photo.created_at,
                "updated_at": photo.updated_at,
            },
            "metadata": {
                "software_used": photo.software_used,
                "copyright": photo.copyright,
            },
            "colors": {
                "dominant_colors": photo.get_dominant_colors_list(),
                "dominant_color_1": photo.dominant_color_1,
                "dominant_color_2": photo.dominant_color_2,
                "dominant_color_3": photo.dominant_color_3,
                "dominant_color_4": photo.dominant_color_4,
                "dominant_color_5": photo.dominant_color_5,
                "colors_extracted": photo.colors_extracted,
                "css_gradient_radial": photo.generate_css_gradient("radial"),
                "css_gradient_linear": photo.generate_css_gradient("linear"),
            },
            "processing_status": {
                "has_dimensions": bool(photo.width and photo.height),
                "has_thumbnail": bool(photo.thumbnail),
                "has_camera_info": bool(photo.camera_make or photo.camera_model),
                "has_exposure_info": bool(photo.iso or photo.aperture or photo.shutter_speed),
                "has_location": bool(photo.latitude and photo.longitude),
                "has_date": bool(photo.date_taken),
                "has_colors": photo.colors_extracted,
                "validation_errors": photo.validate_photo_processing(),
            },
            "user_info": {
                "user_id": photo.user.id,
                "username": photo.user.username,
                "first_name": photo.user.first_name,
                "last_name": photo.user.last_name,
                "email": photo.user.email,
            },
            "collections": {
                "collection_count": photo.collections.count(),
                "collections": [
                    {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description,
                        "is_private": collection.is_private,
                    }
                    for collection in photo.collections.all()
                ],
            },
            "urls": {
                "detail_url": request.build_absolute_uri(f"/photos/photo/{photo.id}/"),
                "edit_url": request.build_absolute_uri(f"/photos/photo/{photo.id}/edit/"),
                "delete_url": request.build_absolute_uri(f"/photos/photo/{photo.id}/delete/"),
                "download_url": request.build_absolute_uri(f"/photos/photo/{photo.id}/download/"),
            },
            "api_endpoints": {
                "photo_detail": request.build_absolute_uri(f"/photos/api/photos/{photo.id}/"),
                "photo_full_detail": request.build_absolute_uri(f"/photos/api/photos/{photo.id}/full/"),
                "photo_delete": request.build_absolute_uri(f"/photos/api/photos/{photo.id}/delete/"),
            }
        }
        
        return Response(comprehensive_data)


class PhotoUploadAPIView(generics.CreateAPIView):
    """API endpoint for uploading photos"""
    serializer_class = PhotoUploadSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def perform_create(self, serializer):
        """Set the user and process the photo"""
        photo = serializer.save(user=self.request.user)
        # Additional processing can be added here if needed
        return photo


class PhotoDeleteAPIView(generics.DestroyAPIView):
    """API endpoint for deleting photos"""
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """Return photos for the authenticated user"""
        return Photo.objects.filter(user=self.request.user)


class CollectionListAPIView(generics.ListCreateAPIView):
    """API endpoint for listing and creating collections"""
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return collections for the authenticated user"""
        return Collection.objects.filter(user=self.request.user).select_related('user')
    
    def perform_create(self, serializer):
        """Set the user when creating a collection"""
        serializer.save(user=self.request.user)


class CollectionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for retrieving, updating and deleting collections"""
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        """Return collections for the authenticated user"""
        return Collection.objects.filter(user=self.request.user).select_related('user')


class CollectionPhotosAPIView(generics.ListAPIView):
    """API endpoint for listing photos in a collection"""
    serializer_class = CollectionPhotoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return photos in the specified collection"""
        collection_id = self.kwargs.get('pk')
        return CollectionPhoto.objects.filter(
            collection_id=collection_id,
            collection__user=self.request.user
        ).select_related('photo', 'collection').order_by('order')


class GalleryAPIView(generics.ListAPIView):
    """API endpoint for the main gallery view"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return photos for the authenticated user with optional filtering"""
        queryset = Photo.objects.filter(user=self.request.user).select_related('user')
        
        # Apply filters if provided
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            queryset = queryset.filter(tags__icontains=tags)
        
        camera_make = self.request.query_params.get('camera_make')
        if camera_make:
            queryset = queryset.filter(camera_make__icontains=camera_make)
        
        camera_model = self.request.query_params.get('camera_model')
        if camera_model:
            queryset = queryset.filter(camera_model__icontains=camera_model)
        
        # Date filtering
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_obj)
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            try:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_obj)
            except ValueError:
                pass
        
        # Sorting
        sort_by = self.request.query_params.get('sort_by', 'date_taken_desc')
        if sort_by == 'date_taken_desc':
            # Sort by date_taken if available, otherwise by created_at
            queryset = queryset.extra(
                select={'sort_date': 'COALESCE(date_taken, created_at)'}
            ).order_by('-sort_date')
        elif sort_by == 'date_taken_asc':
            queryset = queryset.extra(
                select={'sort_date': 'COALESCE(date_taken, created_at)'}
            ).order_by('sort_date')
        elif sort_by == 'date_desc':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'date_asc':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'alphabetical_asc':
            queryset = queryset.order_by('title')
        elif sort_by == 'alphabetical_desc':
            queryset = queryset.order_by('-title')
        
        return queryset


class UserGalleryAPIView(generics.ListAPIView):
    """API endpoint for viewing a specific user's gallery"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return photos for the specified user"""
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            # Only show public photos or photos from the authenticated user
            if self.request.user.is_authenticated and self.request.user.id == user_id:
                return Photo.objects.filter(user=user).select_related('user')
            else:
                # For public viewing, only show non-private photos
                return Photo.objects.filter(
                    user=user,
                    # Add logic here if you have a privacy field
                ).select_related('user')
        except User.DoesNotExist:
            return Photo.objects.none()


class PublicGalleryAPIView(generics.ListAPIView):
    """API endpoint for public gallery (non-authenticated users)"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return public photos from all users"""
        # Add logic here to filter for public photos only
        return Photo.objects.all().select_related('user')[:100]  # Limit for public view


class PhotoSearchAPIView(generics.ListAPIView):
    """API endpoint for searching photos"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return search results for the authenticated user"""
        queryset = Photo.objects.filter(user=self.request.user).select_related('user')
        
        # Get search parameters
        query = self.request.query_params.get('query', '')
        tags = self.request.query_params.get('tags', '')
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(camera_make__icontains=query) |
                Q(camera_model__icontains=query)
            )
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)
        
        return queryset.order_by('-created_at')


class TagListAPIView(generics.ListAPIView):
    """API endpoint for listing all tags"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get(self, request, *args, **kwargs):
        """Return a list of all tags used by the user"""
        user_photos = Photo.objects.filter(user=request.user)
        tags = set()
        
        for photo in user_photos:
            if photo.tags:
                photo_tags = [tag.strip() for tag in photo.tags.split(',')]
                tags.update(photo_tags)
        
        return Response({
            'tags': sorted(list(tags)),
            'count': len(tags)
        })


class PhotosByTagAPIView(generics.ListAPIView):
    """API endpoint for getting photos by tag"""
    serializer_class = PhotoListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Return photos with the specified tag"""
        tag_name = self.kwargs.get('tag_name')
        return Photo.objects.filter(
            user=self.request.user,
            tags__icontains=tag_name
        ).select_related('user').order_by('-created_at')


class PhotoStatsAPIView(generics.ListAPIView):
    """API endpoint for photo statistics"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get(self, request, *args, **kwargs):
        """Return comprehensive photo statistics"""
        user_photos = Photo.objects.filter(user=request.user)
        
        # Basic counts
        total_photos = user_photos.count()
        raw_photos = user_photos.filter(is_raw=True).count()
        jpeg_photos = user_photos.filter(file_extension__in=['jpg', 'jpeg']).count()
        
        # Camera statistics
        camera_makes = user_photos.values('camera_make').exclude(
            camera_make__isnull=True
        ).exclude(camera_make='').annotate(count=Count('camera_make')).order_by('-count')[:5]
        
        camera_models = user_photos.values('camera_model').exclude(
            camera_model__isnull=True
        ).exclude(camera_model='').annotate(count=Count('camera_model')).order_by('-count')[:5]
        
        # Date statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        photos_this_week = user_photos.filter(created_at__date__gte=week_ago).count()
        photos_this_month = user_photos.filter(created_at__date__gte=month_ago).count()
        
        # File size statistics
        total_size = sum(photo.file_size for photo in user_photos)
        avg_size = total_size / total_photos if total_photos > 0 else 0
        
        return Response({
            'total_photos': total_photos,
            'raw_photos': raw_photos,
            'jpeg_photos': jpeg_photos,
            'camera_makes': list(camera_makes),
            'camera_models': list(camera_models),
            'photos_this_week': photos_this_week,
            'photos_this_month': photos_this_month,
            'total_size_bytes': total_size,
            'average_size_bytes': int(avg_size),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'average_size_mb': round(avg_size / (1024 * 1024), 2)
        })


class UserPhotoStatsAPIView(generics.ListAPIView):
    """API endpoint for user-specific photo statistics"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get(self, request, *args, **kwargs):
        """Return photo statistics for a specific user"""
        user_id = self.kwargs.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            user_photos = Photo.objects.filter(user=user)
            
            # Only show stats for public photos or the authenticated user's own photos
            if request.user.is_authenticated and request.user.id == user_id:
                pass  # Show all stats for own photos
            else:
                # For public viewing, only show limited stats
                user_photos = user_photos.filter(
                    # Add logic here if you have a privacy field
                )
            
            total_photos = user_photos.count()
            
            return Response({
                'user_id': user_id,
                'username': user.username,
                'total_photos': total_photos,
                'public_photos': total_photos  # Adjust based on privacy logic
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
