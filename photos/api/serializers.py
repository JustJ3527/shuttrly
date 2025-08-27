from rest_framework import serializers
from django.contrib.auth import get_user_model
from photos.models import Photo, Collection, CollectionPhoto

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class PhotoSerializer(serializers.ModelSerializer):
    """Serializer for Photo model"""
    user = UserSerializer(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()
    dominant_colors = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = [
            'id', 'user', 'title', 'description', 'tags',
            'original_file', 'thumbnail', 'thumbnail_url', 'original_url',
            'file_size', 'file_extension', 'is_raw',
            'width', 'height', 'dominant_colors',
            'camera_make', 'camera_model', 'lens_make', 'lens_model',
            'focal_length', 'focal_length_35mm', 'shutter_speed',
            'aperture', 'iso', 'exposure_bias', 'exposure_mode',
            'metering_mode', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'file_size', 'file_extension', 'width', 'height',
            'dominant_colors', 'camera_make', 'camera_model', 'lens_make',
            'lens_model', 'focal_length', 'focal_length_35mm', 'shutter_speed',
            'aperture', 'iso', 'exposure_bias', 'exposure_mode', 'metering_mode',
            'created_at', 'updated_at'
        ]
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_original_url(self, obj):
        if obj.original_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.original_file.url)
            return obj.original_file.url
        return None
    
    def get_dominant_colors(self, obj):
        """Return dominant colors as a list"""
        colors = []
        if obj.dominant_color_1:
            colors.append(obj.dominant_color_1)
        if obj.dominant_color_2:
            colors.append(obj.dominant_color_2)
        if obj.dominant_color_3:
            colors.append(obj.dominant_color_3)
        if obj.dominant_color_4:
            colors.append(obj.dominant_color_4)
        if obj.dominant_color_5:
            colors.append(obj.dominant_color_5)
        return colors


class PhotoListSerializer(serializers.ModelSerializer):
    """Simplified serializer for photo lists (gallery view)"""
    thumbnail_url = serializers.SerializerMethodField()
    dominant_colors = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = [
            'id', 'title', 'thumbnail_url', 'dominant_colors',
            'width', 'height', 'created_at'
        ]
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_dominant_colors(self, obj):
        colors = []
        if obj.dominant_color_1:
            colors.append(obj.dominant_color_1)
        if obj.dominant_color_2:
            colors.append(obj.dominant_color_2)
        if obj.dominant_color_3:
            colors.append(obj.dominant_color_3)
        return colors


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model"""
    user = UserSerializer(read_only=True)
    photo_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id', 'name', 'description', 'collection_type', 'is_private',
            'user', 'photo_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_photo_count(self, obj):
        return obj.photos.count()


class CollectionPhotoSerializer(serializers.ModelSerializer):
    """Serializer for CollectionPhoto model"""
    photo = PhotoListSerializer(read_only=True)
    
    class Meta:
        model = CollectionPhoto
        fields = ['id', 'photo', 'order', 'added_at']


class PhotoUploadSerializer(serializers.ModelSerializer):
    """Serializer for photo upload"""
    class Meta:
        model = Photo
        fields = ['title', 'description', 'tags', 'original_file']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PhotoSearchSerializer(serializers.Serializer):
    """Serializer for photo search parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    camera_make = serializers.CharField(required=False, allow_blank=True)
    camera_model = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            ('date_desc', 'Newest First'),
            ('date_asc', 'Oldest First'),
            ('alphabetical_asc', 'A-Z'),
            ('alphabetical_desc', 'Z-A'),
        ],
        required=False,
        default='date_desc'
    )
    page = serializers.IntegerField(required=False, default=1)
    page_size = serializers.IntegerField(required=False, default=20)
