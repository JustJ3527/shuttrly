from django.core.management.base import BaseCommand
from photos.models import Photo, PhotoSimilarity
from photos.utils import (
    find_similar_photos,
    find_similar_photos_cached,
    calculate_similarity,
    calculate_pearson_similarity,
    calculate_exif_numeric_similarity,
    calculate_exif_similarity,
    calculate_hybrid_similarity,
    debug_photo_similarity
)


class Command(BaseCommand):
    help = 'Test the advanced similarity system with all methods and caching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-id',
            type=int,
            help='Test with a specific photo ID',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.5,
            help='Similarity threshold (default: 0.5)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of similar photos to return (default: 10)',
        )
        parser.add_argument(
            '--method',
            type=str,
            choices=['cosine', 'pearson'],
            default='cosine',
            help='Similarity method to use (default: cosine)',
        )
        parser.add_argument(
            '--use-cache',
            action='store_true',
            help='Use cached similarities',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear similarity cache before testing',
        )
        parser.add_argument(
            '--compare-methods',
            action='store_true',
            help='Compare cosine vs pearson methods',
        )

    def handle(self, *args, **options):
        # Clear cache if requested
        if options['clear_cache']:
            PhotoSimilarity.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Similarity cache cleared.')
            )
        
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
        
        # Test parameters
        threshold = options['threshold']
        limit = options['limit']
        method = options['method']
        use_cache = options['use_cache']
        
        self.stdout.write(f"\nTest parameters:")
        self.stdout.write(f"  - Method: {method}")
        self.stdout.write(f"  - Threshold: {threshold}")
        self.stdout.write(f"  - Limit: {limit}")
        self.stdout.write(f"  - Use cache: {use_cache}")
        
        # Test individual similarity functions
        self.stdout.write(f"\n=== TESTING INDIVIDUAL SIMILARITY FUNCTIONS ===")
        
        # Get a few other photos for comparison
        other_photos = photos_with_embeddings.exclude(id=test_photo.id)[:3]
        
        for i, other_photo in enumerate(other_photos, 1):
            self.stdout.write(f"\n--- Comparison {i}: Photo {other_photo.id} ---")
            
            # Visual similarity
            visual_cosine = calculate_similarity(test_photo.embedding, other_photo.embedding)
            visual_pearson = calculate_pearson_similarity(test_photo.embedding, other_photo.embedding)
            
            # EXIF numeric similarity
            exif_numeric_cosine = calculate_exif_numeric_similarity(test_photo, other_photo, "cosine")
            exif_numeric_pearson = calculate_exif_numeric_similarity(test_photo, other_photo, "pearson")
            
            # Full EXIF similarity
            exif_cosine = calculate_exif_similarity(test_photo, other_photo, method="cosine")
            exif_pearson = calculate_exif_similarity(test_photo, other_photo, method="pearson")
            
            # Hybrid similarity
            hybrid_cosine = calculate_hybrid_similarity(test_photo, other_photo, method="cosine")
            hybrid_pearson = calculate_hybrid_similarity(test_photo, other_photo, method="pearson")
            
            self.stdout.write(f"  Visual (cosine): {visual_cosine:.3f}")
            self.stdout.write(f"  Visual (pearson): {visual_pearson:.3f}")
            self.stdout.write(f"  EXIF numeric (cosine): {exif_numeric_cosine:.3f}")
            self.stdout.write(f"  EXIF numeric (pearson): {exif_numeric_pearson:.3f}")
            self.stdout.write(f"  EXIF full (cosine): {exif_cosine:.3f}")
            self.stdout.write(f"  EXIF full (pearson): {exif_pearson:.3f}")
            self.stdout.write(f"  Hybrid (cosine): {hybrid_cosine:.3f}")
            self.stdout.write(f"  Hybrid (pearson): {hybrid_pearson:.3f}")
        
        # Test similarity search
        self.stdout.write(f"\n=== TESTING SIMILARITY SEARCH ===")
        
        try:
            if use_cache:
                similar_results = find_similar_photos_cached(
                    test_photo,
                    limit=limit,
                    threshold=threshold,
                    method=method,
                    use_cache=True
                )
                self.stdout.write(f"Using cached similarity search")
            else:
                similar_results = find_similar_photos(
                    test_photo,
                    limit=limit,
                    threshold=threshold,
                    method=method
                )
                self.stdout.write(f"Using direct similarity search")
            
            self.stdout.write(f"\nFound {len(similar_results)} similar photos:")
            
            for i, result in enumerate(similar_results, 1):
                photo = result['photo']
                self.stdout.write(f"  {i}. Photo {photo.id}: '{photo.title}'")
                self.stdout.write(f"     - Visual: {result['visual']:.3f}")
                self.stdout.write(f"     - EXIF: {result['exif']:.3f}")
                self.stdout.write(f"     - Final: {result['final']:.3f}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during similarity search: {str(e)}')
            )
            import traceback
            traceback.print_exc()
        
        # Compare methods if requested
        if options['compare_methods']:
            self.stdout.write(f"\n=== COMPARING COSINE VS PEARSON ===")
            
            try:
                # Test with cosine
                cosine_results = find_similar_photos(
                    test_photo,
                    limit=5,
                    threshold=threshold,
                    method="cosine"
                )
                
                # Test with pearson
                pearson_results = find_similar_photos(
                    test_photo,
                    limit=5,
                    threshold=threshold,
                    method="pearson"
                )
                
                self.stdout.write(f"\nCosine method results:")
                for i, result in enumerate(cosine_results, 1):
                    self.stdout.write(f"  {i}. Photo {result['photo'].id}: {result['final']:.3f}")
                
                self.stdout.write(f"\nPearson method results:")
                for i, result in enumerate(pearson_results, 1):
                    self.stdout.write(f"  {i}. Photo {result['photo'].id}: {result['final']:.3f}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error comparing methods: {str(e)}')
                )
        
        # Cache statistics
        if use_cache:
            cache_count = PhotoSimilarity.objects.count()
            self.stdout.write(f"\nCache statistics:")
            self.stdout.write(f"  - Total cached similarities: {cache_count}")
            
            if cache_count > 0:
                cosine_count = PhotoSimilarity.objects.filter(method="cosine").count()
                pearson_count = PhotoSimilarity.objects.filter(method="pearson").count()
                self.stdout.write(f"  - Cosine similarities: {cosine_count}")
                self.stdout.write(f"  - Pearson similarities: {pearson_count}")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Test completed successfully!')}")
