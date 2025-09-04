from django.core.management.base import BaseCommand
from photos.models import Photo
from photos.utils import find_similar_photos, debug_photo_similarity


class Command(BaseCommand):
    help = 'Test the hybrid similarity system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-id',
            type=int,
            help='Test with a specific photo ID',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.1,
            help='Similarity threshold (default: 0.1)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of similar photos to return (default: 10)',
        )

    def handle(self, *args, **options):
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        )
        
        if not photos_with_embeddings.exists():
            self.stdout.write(
                self.style.ERROR('No photos with embeddings found. Please generate embeddings first.')
            )
            return
        
        self.stdout.write(f"Found {photos_with_embeddings.count()} photos with embeddings")
        
        # Get test photo
        if options['photo_id']:
            try:
                test_photo = photos_with_embeddings.get(id=options['photo_id'])
            except Photo.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Photo with ID {options["photo_id"]} not found or has no embedding')
                )
                return
        else:
            test_photo = photos_with_embeddings.first()
        
        self.stdout.write(f"\nTesting with photo ID: {test_photo.id}")
        self.stdout.write(f"Photo title: {test_photo.title}")
        
        # Debug photo data
        debug_photo_similarity(test_photo)
        
        # Test similarity search
        threshold = options['threshold']
        limit = options['limit']
        
        self.stdout.write(f"\nSearching for similar photos (threshold: {threshold}, limit: {limit})")
        
        try:
            similar_results = find_similar_photos(
                test_photo,
                limit=limit,
                threshold=threshold
            )
            
            self.stdout.write(f"\nFound {len(similar_results)} similar photos:")
            
            for i, result in enumerate(similar_results, 1):
                photo = result['photo']
                similarity = result['similarity']
                self.stdout.write(
                    f"  {i}. Photo {photo.id}: '{photo.title}' (similarity: {similarity:.3f})"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during similarity search: {str(e)}')
            )
            import traceback
            traceback.print_exc()
