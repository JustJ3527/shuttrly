from django.core.management.base import BaseCommand
from photos.models import Photo, PhotoSimilarity
from photos.utils import (
    find_similar_photos_cached,
    calculate_similarity,
    calculate_pearson_similarity,
    calculate_exif_similarity,
    calculate_hybrid_similarity
)


class Command(BaseCommand):
    help = 'Compare all similarity methods side by side'

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
            default=5,
            help='Maximum number of similar photos to return (default: 5)',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear similarity cache before testing',
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
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"TESTING PHOTO: {test_photo.title} (ID: {test_photo.id})")
        self.stdout.write(f"{'='*60}")
        
        # Test parameters
        threshold = options['threshold']
        limit = options['limit']
        
        self.stdout.write(f"\nParameters:")
        self.stdout.write(f"  - Threshold: {threshold}")
        self.stdout.write(f"  - Limit: {limit}")
        
        # Test all methods
        methods_to_test = [
            ('cosine', 'Cosine Similarity'),
            ('pearson', 'Pearson Correlation'),
        ]
        
        results = {}
        
        for method_key, method_name in methods_to_test:
            self.stdout.write(f"\n{'-'*40}")
            self.stdout.write(f"TESTING: {method_name}")
            self.stdout.write(f"{'-'*40}")
            
            try:
                # Test hybrid similarity
                similar_results = find_similar_photos_cached(
                    test_photo,
                    limit=limit,
                    threshold=threshold,
                    method=method_key,
                    use_cache=True
                )
                
                results[method_key] = similar_results
                
                self.stdout.write(f"\nFound {len(similar_results)} similar photos:")
                
                for i, result in enumerate(similar_results, 1):
                    photo = result['photo']
                    self.stdout.write(f"  {i}. Photo {photo.id}: '{photo.title}'")
                    self.stdout.write(f"     - Visual: {result['visual']:.3f}")
                    self.stdout.write(f"     - EXIF: {result['exif']:.3f}")
                    self.stdout.write(f"     - Final: {result['final']:.3f}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error testing {method_name}: {str(e)}')
                )
                results[method_key] = []
        
        # Compare results
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"COMPARISON SUMMARY")
        self.stdout.write(f"{'='*60}")
        
        # Find common photos between methods
        cosine_photos = {result['photo'].id for result in results.get('cosine', [])}
        pearson_photos = {result['photo'].id for result in results.get('pearson', [])}
        
        common_photos = cosine_photos & pearson_photos
        cosine_only = cosine_photos - pearson_photos
        pearson_only = pearson_photos - cosine_photos
        
        self.stdout.write(f"\nResults comparison:")
        self.stdout.write(f"  - Cosine only: {len(cosine_only)} photos")
        self.stdout.write(f"  - Pearson only: {len(pearson_only)} photos")
        self.stdout.write(f"  - Common to both: {len(common_photos)} photos")
        
        if common_photos:
            self.stdout.write(f"\nCommon photos:")
            for photo_id in sorted(common_photos):
                # Find the photo in both results
                cosine_result = next((r for r in results.get('cosine', []) if r['photo'].id == photo_id), None)
                pearson_result = next((r for r in results.get('pearson', []) if r['photo'].id == photo_id), None)
                
                if cosine_result and pearson_result:
                    self.stdout.write(f"  Photo {photo_id}:")
                    self.stdout.write(f"    Cosine final: {cosine_result['final']:.3f}")
                    self.stdout.write(f"    Pearson final: {pearson_result['final']:.3f}")
                    self.stdout.write(f"    Difference: {abs(cosine_result['final'] - pearson_result['final']):.3f}")
        
        # Cache statistics
        cache_count = PhotoSimilarity.objects.count()
        self.stdout.write(f"\nCache statistics:")
        self.stdout.write(f"  - Total cached similarities: {cache_count}")
        
        if cache_count > 0:
            cosine_count = PhotoSimilarity.objects.filter(method="cosine").count()
            pearson_count = PhotoSimilarity.objects.filter(method="pearson").count()
            self.stdout.write(f"  - Cosine similarities: {cosine_count}")
            self.stdout.write(f"  - Pearson similarities: {pearson_count}")
        
        self.stdout.write(f"\n{self.style.SUCCESS('Comparison completed successfully!')}")
        
        # Recommendations
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"RECOMMENDATIONS")
        self.stdout.write(f"{'='*60}")
        
        if len(common_photos) > len(cosine_only) and len(common_photos) > len(pearson_only):
            self.stdout.write("✅ Both methods show good agreement - either can be used")
        elif len(cosine_only) > len(pearson_only):
            self.stdout.write("📊 Cosine similarity finds more unique results")
        elif len(pearson_only) > len(cosine_only):
            self.stdout.write("📈 Pearson correlation finds more unique results")
        
        if cache_count > 0:
            self.stdout.write("💾 Cache is working - performance is optimized")
        else:
            self.stdout.write("⚠️  No cache entries - consider running with --use-cache")
