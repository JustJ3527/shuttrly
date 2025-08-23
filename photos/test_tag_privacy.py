"""
Test file for tag privacy functionality

This file tests the logic for displaying photos and collections based on user privacy settings.
The tests verify that:
1. Private users only see their own content
2. Public users see all public content from all users
3. Proper access control is enforced
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from photos.models import Photo, Collection
from photos.forms import PhotoUploadForm

User = get_user_model()

class TagPrivacyTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        
        # Set user1 as public, user2 as private
        self.user1.is_private = False
        self.user1.save()
        self.user2.is_private = True
        self.user2.save()
        
        # Create test photos
        self.photo1_public = Photo.objects.create(
            user=self.user1,
            title='Public Photo 1',
            description='A public photo by user1',
            tags='#nature #landscape',
            is_private=False,
            file_size=1024,
            file_extension='jpg'
        )
        
        self.photo1_private = Photo.objects.create(
            user=self.user1,
            title='Private Photo 1',
            description='A private photo by user1',
            tags='#nature #wildlife',
            is_private=True,
            file_size=1024,
            file_extension='jpg'
        )
        
        self.photo2_public = Photo.objects.create(
            user=self.user2,
            title='Public Photo 2',
            description='A public photo by user2',
            tags='#nature #landscape',
            is_private=False,
            file_size=1024,
            file_extension='jpg'
        )
        
        self.photo2_private = Photo.objects.create(
            user=self.user2,
            title='Private Photo 2',
            description='A private photo by user2',
            tags='#nature #wildlife',
            is_private=True,
            file_size=1024,
            file_extension='jpg'
        )
        
        # Create test collections
        self.collection1_public = Collection.objects.create(
            name='Public Collection 1',
            description='A public collection by user1',
            owner=self.user1,
            is_private=False,
            tags='#nature #landscape'
        )
        
        self.collection1_private = Collection.objects.create(
            name='Private Collection 1',
            description='A private collection by user1',
            owner=self.user1,
            is_private=True,
            tags='#nature #wildlife'
        )
        
        self.collection2_public = Collection.objects.create(
            name='Public Collection 2',
            description='A public collection by user2',
            owner=self.user2,
            is_private=False,
            tags='#nature #landscape'
        )
        
        self.collection2_private = Collection.objects.create(
            name='Private Collection 2',
            description='A private collection by user2',
            owner=self.user2,
            is_private=True,
            tags='#nature #wildlife'
        )
        
        # Set up client
        self.client = Client()
    
    def test_tag_detail_public_user(self):
        """Test that public users can see all public content with a tag"""
        # Login as public user
        self.client.force_login(self.user1)
        
        # Test tag detail view for 'nature' tag
        response = self.client.get(reverse('photos:tag_detail', kwargs={'tag_name': 'nature'}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Photo 1')  # Own public photo
        self.assertContains(response, 'Public Photo 2')  # Other user's public photo
        self.assertNotContains(response, 'Private Photo 1')  # Own private photo
        self.assertNotContains(response, 'Private Photo 2')  # Other user's private photo
        
        # Check collections
        self.assertContains(response, 'Public Collection 1')  # Own public collection
        self.assertContains(response, 'Public Collection 2')  # Other user's public collection
        self.assertNotContains(response, 'Private Collection 1')  # Own private collection
        self.assertNotContains(response, 'Private Collection 2')  # Other user's private collection
    
    def test_tag_detail_private_user(self):
        """Test that private users only see their own content with a tag"""
        # Login as private user
        self.client.force_login(self.user2)
        
        # Test tag detail view for 'nature' tag
        response = self.client.get(reverse('photos:tag_detail', kwargs={'tag_name': 'nature'}))
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Public Photo 1')  # Other user's public photo
        self.assertContains(response, 'Public Photo 2')  # Own public photo
        self.assertNotContains(response, 'Private Photo 1')  # Other user's private photo
        self.assertContains(response, 'Private Photo 2')  # Own private photo
        
        # Check collections
        self.assertNotContains(response, 'Public Collection 1')  # Other user's public collection
        self.assertContains(response, 'Public Collection 2')  # Own public collection
        self.assertNotContains(response, 'Private Collection 1')  # Other user's private collection
        self.assertContains(response, 'Private Collection 2')  # Own private collection
    
    def test_search_by_tags_public_user(self):
        """Test that public users can search all public content by tags"""
        # Login as public user
        self.client.force_login(self.user1)
        
        # Test search by tags
        response = self.client.get(reverse('photos:search_by_tags'), {'tags': 'nature landscape'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Photo 1')  # Own public photo
        self.assertContains(response, 'Public Photo 2')  # Other user's public photo
        self.assertContains(response, 'Public Collection 1')  # Own public collection
        self.assertContains(response, 'Public Collection 2')  # Other user's public collection
    
    def test_search_by_tags_private_user(self):
        """Test that private users only search their own content by tags"""
        # Login as private user
        self.client.force_login(self.user2)
        
        # Test search by tags
        response = self.client.get(reverse('photos:search_by_tags'), {'tags': 'nature landscape'})
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Public Photo 1')  # Other user's public photo
        self.assertContains(response, 'Public Photo 2')  # Own public photo
        self.assertNotContains(response, 'Public Collection 1')  # Other user's public collection
        self.assertContains(response, 'Public Collection 2')  # Own public collection
    
    def test_photo_detail_access_control(self):
        """Test access control for photo detail views"""
        # Test that public users can access public photos from other users
        self.client.force_login(self.user1)
        response = self.client.get(reverse('photos:detail', kwargs={'photo_id': self.photo2_public.id}))
        self.assertEqual(response.status_code, 200)
        
        # Test that private users cannot access private photos from other users
        self.client.force_login(self.user2)
        response = self.client.get(reverse('photos:detail', kwargs={'photo_id': self.photo1_private.id}))
        self.assertEqual(response.status_code, 302)  # Redirect to gallery
    
    def test_collection_detail_access_control(self):
        """Test access control for collection detail views"""
        # Test that public users can access public collections from other users
        self.client.force_login(self.user1)
        response = self.client.get(reverse('photos:collection_detail', kwargs={'collection_id': self.collection2_public.id}))
        self.assertEqual(response.status_code, 200)
        
        # Test that private users cannot access private collections from other users
        self.client.force_login(self.user2)
        response = self.client.get(reverse('photos:collection_detail', kwargs={'collection_id': self.collection1_private.id}))
        self.assertEqual(response.status_code, 302)  # Redirect to collection list

if __name__ == '__main__':
    # Run tests
    import django
    django.setup()
    
    # Create test suite
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run tests
    failures = test_runner.run_tests(['photos.test_tag_privacy'])
    
    if failures:
        print(f"Tests failed: {failures}")
    else:
        print("All tests passed!")

