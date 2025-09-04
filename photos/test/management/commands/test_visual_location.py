from django.core.management.base import BaseCommand
from photos.models import Photo
from photos.utils import find_similar_photos_visual_location, calculate_visual_location_similarity

class Command(BaseCommand):
    help = 'Test the Visual + Location similarity system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Visual + Location Similarity System'))
        
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        ).order_by('id')
        
        if not photos_with_embeddings.exists():
            self.stdout.write(self.style.ERROR('No photos with embeddings found!'))
            return
        
        self.stdout.write(f"Found {photos_with_embeddings.count()} photos with embeddings")
        
        # Test with first photo
        test_photo = photos_with_embeddings.first()
        self.stdout.write(f"\nTesting with photo {test_photo.id}: {test_photo.title}")
        
        # Show photo location info
        if test_photo.latitude and test_photo.longitude:
            self.stdout.write(f"Location: {test_photo.latitude}, {test_photo.longitude}")
        else:
            self.stdout.write("No location data")
        
        # Test visual + location similarity
        self.stdout.write(f"\n=== Visual + Location Similarity Results ===")
        results = find_similar_photos_visual_location(
            test_photo, 
            limit=5, 
            threshold=0.3,
            method="cosine"
        )
        
        if results:
            for i, result in enumerate(results, 1):
                photo = result['photo']
                visual = result['visual']
                location = result['location']
                final = result['final']
                
                self.stdout.write(f"{i}. Photo {photo.id}: {photo.title}")
                self.stdout.write(f"   Visual: {visual:.3f}, Location: {location:.3f}, Final: {final:.3f}")
                if photo.latitude and photo.longitude:
                    self.stdout.write(f"   Location: {photo.latitude}, {photo.longitude}")
                else:
                    self.stdout.write(f"   No location data")
        else:
            self.stdout.write("No similar photos found")
        
        # Test individual similarity calculation
        self.stdout.write(f"\n=== Individual Similarity Tests ===")
        other_photos = photos_with_embeddings.exclude(id=test_photo.id)[:3]
        
        for other_photo in other_photos:
            similarity = calculate_visual_location_similarity(test_photo, other_photo, method="cosine")
            self.stdout.write(f"Photo {test_photo.id} vs Photo {other_photo.id}: {similarity:.3f}")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Visual + Location similarity test completed!')}")
