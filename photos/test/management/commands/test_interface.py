from django.core.management.base import BaseCommand
from photos.models import Photo


class Command(BaseCommand):
    help = 'Test the interface by checking photo data and URLs'

    def handle(self, *args, **options):
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        ).order_by('id')
        
        if not photos_with_embeddings.exists():
            self.stdout.write(self.style.ERROR('No photos with embeddings found.'))
            return
        
        self.stdout.write(f"✅ Found {photos_with_embeddings.count()} photos with embeddings")
        
        # Show first 10 photos
        self.stdout.write(f"\n📸 First 10 photos available:")
        for i, photo in enumerate(photos_with_embeddings[:10]):
            self.stdout.write(f"  {i+1:2d}. ID: {photo.id:3d} - {photo.title}")
        
        # Test URLs
        self.stdout.write(f"\n🔗 Test URLs:")
        base_url = "http://localhost:8000/photos/test-advanced/"
        self.stdout.write(f"  Base URL: {base_url}")
        
        for photo in photos_with_embeddings[:5]:
            url = f"{base_url}{photo.id}/"
            self.stdout.write(f"  Photo {photo.id}: {url}")
        
        # Test with parameters
        test_photo = photos_with_embeddings.first()
        params_url = f"{base_url}{test_photo.id}/?threshold=0.5&limit=10&use_cache=true"
        self.stdout.write(f"  With params: {params_url}")
        
        # Check EXIF data for first few photos
        self.stdout.write(f"\n📊 EXIF Data for first 5 photos:")
        for photo in photos_with_embeddings[:5]:
            self.stdout.write(f"  Photo {photo.id}:")
            self.stdout.write(f"    Camera: {photo.camera_make} {photo.camera_model}")
            self.stdout.write(f"    Date: {photo.date_taken}")
            self.stdout.write(f"    ISO: {photo.iso}")
            self.stdout.write(f"    Aperture: {photo.aperture}")
            self.stdout.write(f"    Shutter: {photo.shutter_speed}")
            self.stdout.write()
        
        self.stdout.write(f"\n🎯 Instructions:")
        self.stdout.write(f"1. Start the server: python manage.py runserver")
        self.stdout.write(f"2. Go to: {base_url}")
        self.stdout.write(f"3. Use the dropdown to select different photos")
        self.stdout.write(f"4. Use Previous/Next buttons or arrow keys")
        self.stdout.write(f"5. Check browser console for debug info")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Interface test completed!')}")
