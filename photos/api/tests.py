from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from photos.models import Photo, Collection
from photos.api.serializers import PhotoSerializer, PhotoListSerializer
import tempfile
import os
from PIL import Image

User = get_user_model()


class PhotosAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test photo
        self.photo = Photo.objects.create(
            user=self.user,
            title='Test Photo',
            description='A test photo',
            tags='test, photo, api',
            file_size=1024000,
            file_extension='jpg',
            is_raw=False,
            width=1920,
            height=1080
        )
        
        # Create test collection
        self.collection = Collection.objects.create(
            user=self.user,
            name='Test Collection',
            description='A test collection',
            collection_type='personal',
            is_private=False
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def test_photo_list_api(self):
        """Test photo list API endpoint"""
        url = reverse('photos_api:photo-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_photo_detail_api(self):
        """Test photo detail API endpoint"""
        url = reverse('photos_api:photo-detail', args=[self.photo.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.photo.id)
        self.assertEqual(response.data['title'], self.photo.title)
    
    def test_photo_search_api(self):
        """Test photo search API endpoint"""
        url = reverse('photos_api:photo-search')
        response = self.client.get(url, {'query': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_gallery_api(self):
        """Test gallery API endpoint"""
        url = reverse('photos_api:gallery')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_collection_list_api(self):
        """Test collection list API endpoint"""
        url = reverse('photos_api:collection-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_collection_detail_api(self):
        """Test collection detail API endpoint"""
        url = reverse('photos_api:collection-detail', args=[self.collection.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.collection.id)
        self.assertEqual(response.data['name'], self.collection.name)
    
    def test_tags_api(self):
        """Test tags API endpoint"""
        url = reverse('photos_api:tag-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tags', response.data)
        self.assertIn('count', response.data)
    
    def test_photo_stats_api(self):
        """Test photo stats API endpoint"""
        url = reverse('photos_api:photo-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_photos', response.data)
        self.assertEqual(response.data['total_photos'], 1)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        # Unauthenticate client
        self.client.force_authenticate(user=None)
        
        url = reverse('photos_api:photo-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_photo_filtering(self):
        """Test photo filtering by tags"""
        url = reverse('photos_api:gallery')
        response = self.client.get(url, {'tags': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_photo_sorting(self):
        """Test photo sorting"""
        url = reverse('photos_api:gallery')
        response = self.client.get(url, {'sort_by': 'date_desc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_pagination(self):
        """Test API pagination"""
        # Create additional photos
        for i in range(25):
            Photo.objects.create(
                user=self.user,
                title=f'Photo {i}',
                file_size=1024000,
                file_extension='jpg',
                is_raw=False
            )
        
        url = reverse('photos_api:photo-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 26)  # 25 new + 1 original


class PhotoSerializerTestCase(TestCase):
    def setUp(self):
        """Set up test data for serializers"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.photo = Photo.objects.create(
            user=self.user,
            title='Test Photo',
            description='A test photo',
            tags='test, photo, api',
            file_size=1024000,
            file_extension='jpg',
            is_raw=False,
            width=1920,
            height=1080,
            dominant_color_1='#FF0000',
            dominant_color_2='#00FF00',
            dominant_color_3='#0000FF'
        )
    
    def test_photo_serializer(self):
        """Test PhotoSerializer"""
        serializer = PhotoSerializer(self.photo)
        data = serializer.data
        
        self.assertEqual(data['id'], self.photo.id)
        self.assertEqual(data['title'], self.photo.title)
        self.assertEqual(data['description'], self.photo.description)
        self.assertEqual(data['tags'], self.photo.tags)
        self.assertIn('dominant_colors', data)
        self.assertEqual(len(data['dominant_colors']), 3)
    
    def test_photo_list_serializer(self):
        """Test PhotoListSerializer"""
        serializer = PhotoListSerializer(self.photo)
        data = serializer.data
        
        self.assertEqual(data['id'], self.photo.id)
        self.assertEqual(data['title'], self.photo.title)
        self.assertIn('dominant_colors', data)
        self.assertNotIn('description', data)  # Should not be included in list view


class PhotoAPIIntegrationTestCase(APITestCase):
    def setUp(self):
        """Set up integration test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_photo_upload_flow(self):
        """Test complete photo upload flow"""
        # This would test the actual photo upload process
        # For now, we'll test the endpoint structure
        url = reverse('photos_api:photo-upload')
        
        # Test that the endpoint exists and is accessible
        response = self.client.get(url)
        # GET might not be allowed for upload endpoint, but we can test the URL structure
        self.assertIn(url, str(response.url) if hasattr(response, 'url') else '')
    
    def test_photo_delete_flow(self):
        """Test photo deletion flow"""
        # Create a photo to delete
        photo = Photo.objects.create(
            user=self.user,
            title='Delete Test Photo',
            file_size=1024000,
            file_extension='jpg',
            is_raw=False
        )
        
        url = reverse('photos_api:photo-delete', args=[photo.id])
        response = self.client.delete(url)
        
        # Check if photo was deleted
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Photo.objects.filter(id=photo.id).exists())
