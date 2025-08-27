from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the photo.
        return obj.user == request.user


class IsCollectionOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow collection owners to edit collections.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the collection
        return obj.user == request.user


class PhotoUploadPermission(permissions.BasePermission):
    """
    Permission for photo upload - only authenticated users can upload.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can upload photos
        return request.user and request.user.is_authenticated


class PublicGalleryPermission(permissions.BasePermission):
    """
    Permission for public gallery - anyone can view public photos.
    """
    
    def has_permission(self, request, view):
        # Anyone can view public gallery
        return True
