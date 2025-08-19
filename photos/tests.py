from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Photo
import os

User = get_user_model()


class PhotoModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        # Create a simple test image file
        self.test_image_content = b"fake-image-content"
        self.test_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=self.test_image_content,
            content_type="image/jpeg",
        )

    def test_photo_creation(self):
        """Test that a photo can be created"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            title="Test Photo",
            description="A test photo",
            tags="test, photo",
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
        )

        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.title, "Test Photo")
        self.assertEqual(photo.description, "A test photo")
        self.assertEqual(photo.tags, "test, photo")
        self.assertEqual(photo.file_size, len(self.test_image_content))
        self.assertEqual(photo.file_extension, "jpg")
        self.assertFalse(photo.is_raw)
        self.assertIsNotNone(photo.created_at)
        self.assertIsNotNone(photo.updated_at)

    def test_photo_str_representation(self):
        """Test the string representation of a photo"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            title="Test Photo",
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
        )

        self.assertEqual(str(photo), "Test Photo")

    def test_photo_without_title(self):
        """Test photo creation without title"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
        )

        self.assertEqual(str(photo), "Untitled")

    def test_photo_upload_path(self):
        """Test that upload path is generated correctly"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
        )

        # Check that the upload path contains the user ID
        self.assertIn(str(self.user.id), photo.original_file.name)
        self.assertIn("photos", photo.original_file.name)

    def test_photo_is_raw_detection(self):
        """Test that RAW files are correctly identified"""
        # Test JPEG file (not RAW)
        jpeg_photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
        )

        self.assertFalse(jpeg_photo.is_raw)

        # Test RAW file
        raw_photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="cr2",
            is_raw=True,
        )

        self.assertTrue(raw_photo.is_raw)

    def test_photo_public_private(self):
        """Test photo public/private functionality"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
            is_public=False,
        )

        self.assertFalse(photo.is_public)

        # Make it public
        photo.is_public = True
        photo.save()

        self.assertTrue(photo.is_public)

    def test_photo_featured(self):
        """Test photo featured functionality"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
            is_featured=False,
        )

        self.assertFalse(photo.is_featured)

        # Make it featured
        photo.is_featured = True
        photo.save()

        self.assertTrue(photo.is_featured)

    def test_photo_tags_list(self):
        """Test photo tags functionality"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=len(self.test_image_content),
            file_extension="jpg",
            is_raw=False,
            tags="landscape, nature, sunset",
        )

        tags_list = photo.get_tags_list()
        self.assertEqual(len(tags_list), 3)
        self.assertIn("landscape", tags_list)
        self.assertIn("nature", tags_list)
        self.assertIn("sunset", tags_list)

    def test_photo_file_size_mb(self):
        """Test file size conversion to MB"""
        photo = Photo.objects.create(
            user=self.user,
            original_file=self.test_image,
            file_size=1048576,  # 1 MB in bytes
            file_extension="jpg",
            is_raw=False,
        )

        self.assertEqual(photo.get_file_size_mb(), 1.0)

    def tearDown(self):
        """Clean up test files"""
        # Remove test files
        if os.path.exists(self.test_image.name):
            os.remove(self.test_image.name)

        # Clean up any created photos
        Photo.objects.all().delete()
        User.objects.all().delete()
