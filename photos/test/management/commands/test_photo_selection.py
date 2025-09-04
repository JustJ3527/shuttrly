from django.core.management.base import BaseCommand
from photos.models import Photo


class Command(BaseCommand):
    help = 'Test photo selection with different IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-ids',
            nargs='+',
            type=int,
            default=[2, 3, 4, 5, 6],
            help='Photo IDs to test (default: 2 3 4 5 6)',
        )

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
        
        # Test specific photo IDs
        test_ids = options['test_ids']
        self.stdout.write(f"\n🧪 Testing photo IDs: {test_ids}")
        
        for photo_id in test_ids:
            try:
                photo = photos_with_embeddings.get(id=photo_id)
                self.stdout.write(f"✅ Photo {photo_id}: {photo.title}")
                self.stdout.write(f"   Camera: {photo.camera_make} {photo.camera_model}")
                self.stdout.write(f"   Date: {photo.date_taken}")
                self.stdout.write(f"   Embedding length: {len(photo.embedding) if photo.embedding else 0}")
                
                # Generate test URL
                test_url = f"http://localhost:8000/photos/test-advanced/?photo_id={photo_id}&threshold=0.5&limit=10&use_cache=true"
                self.stdout.write(f"   Test URL: {test_url}")
                self.stdout.write()
                
            except Photo.DoesNotExist:
                self.stdout.write(f"❌ Photo {photo_id}: Not found")
                self.stdout.write()
        
        # Show available photo IDs
        self.stdout.write(f"📸 Available photo IDs (first 20):")
        available_ids = [photo.id for photo in photos_with_embeddings[:20]]
        self.stdout.write(f"   {available_ids}")
        
        self.stdout.write(f"\n🎯 Test Instructions:")
        self.stdout.write(f"1. Start server: python manage.py runserver")
        self.stdout.write(f"2. Go to: http://localhost:8000/photos/test-advanced/")
        self.stdout.write(f"3. Change photo ID in the input field")
        self.stdout.write(f"4. Press Enter or click 'Tester'")
        self.stdout.write(f"5. Verify the photo changes and ID is correct")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Photo selection test completed!')}")
