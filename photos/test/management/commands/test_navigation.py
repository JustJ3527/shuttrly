from django.core.management.base import BaseCommand
from photos.models import Photo


class Command(BaseCommand):
    help = 'Test navigation and photo selection for the advanced similarity interface'

    def handle(self, *args, **options):
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        ).order_by('id')
        
        if not photos_with_embeddings.exists():
            self.stdout.write(
                self.style.ERROR('No photos with embeddings found.')
            )
            return
        
        self.stdout.write(f"Found {photos_with_embeddings.count()} photos with embeddings")
        
        # Show first 20 photos for testing
        self.stdout.write(f"\nFirst 20 photos available for testing:")
        for i, photo in enumerate(photos_with_embeddings[:20]):
            self.stdout.write(f"  {i+1:2d}. ID: {photo.id:3d} - {photo.title}")
        
        # Test navigation logic
        self.stdout.write(f"\nTesting navigation logic:")
        photos_list = list(photos_with_embeddings)
        
        for i in [0, 1, 2, len(photos_list)-2, len(photos_list)-1]:
            if i < len(photos_list):
                current_photo = photos_list[i]
                prev_photo = photos_list[i-1] if i > 0 else None
                next_photo = photos_list[i+1] if i < len(photos_list)-1 else None
                
                self.stdout.write(f"  Position {i+1}:")
                self.stdout.write(f"    Current: Photo {current_photo.id} - {current_photo.title}")
                self.stdout.write(f"    Previous: {'Photo ' + str(prev_photo.id) + ' - ' + prev_photo.title if prev_photo else 'None'}")
                self.stdout.write(f"    Next: {'Photo ' + str(next_photo.id) + ' - ' + next_photo.title if next_photo else 'None'}")
                self.stdout.write()
        
        # Test URL generation
        self.stdout.write(f"Example URLs for testing:")
        test_photo = photos_list[0]
        self.stdout.write(f"  Base URL: /photos/test-advanced/")
        self.stdout.write(f"  With photo ID: /photos/test-advanced/{test_photo.id}/")
        self.stdout.write(f"  With parameters: /photos/test-advanced/{test_photo.id}/?threshold=0.5&limit=10&use_cache=true")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Navigation test completed!')}")
        self.stdout.write(f"\nTo test the interface:")
        self.stdout.write(f"1. Go to: http://localhost:8000/photos/test-advanced/")
        self.stdout.write(f"2. Use the photo dropdown to select different photos")
        self.stdout.write(f"3. Use the Previous/Next buttons or arrow keys")
        self.stdout.write(f"4. Check the browser console for debug information")
