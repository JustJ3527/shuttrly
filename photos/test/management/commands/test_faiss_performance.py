"""
Django management command to test FAISS performance vs brute force.

This command compares the performance and results of FAISS-based similarity
search against brute force comparison for the Visual + Location model.
"""

from django.core.management.base import BaseCommand
from photos.models import Photo
from photos.utils import find_similar_photos_visual_location
import time


class Command(BaseCommand):
    help = 'Test FAISS performance vs brute force for Visual + Location similarity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-id',
            type=int,
            help='Specific photo ID to test (default: first photo with embedding)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of similar photos to find (default: 10)'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.5,
            help='Similarity threshold (default: 0.5)'
        )

    def handle(self, *args, **options):
        photo_id = options.get('photo_id')
        limit = options.get('limit')
        threshold = options.get('threshold')

        self.stdout.write(self.style.SUCCESS('FAISS Performance Test'))
        self.stdout.write('=' * 50)

        # Get test photo
        if photo_id:
            try:
                test_photo = Photo.objects.get(id=photo_id)
                if not test_photo.embedding:
                    raise CommandError(f'Photo {photo_id} has no embedding')
            except Photo.DoesNotExist:
                raise CommandError(f'Photo {photo_id} not found')
        else:
            # Get first photo with embedding
            test_photo = Photo.objects.exclude(
                embedding__isnull=True
            ).exclude(
                embedding=[]
            ).first()
            
            if not test_photo:
                raise CommandError('No photos with embeddings found')

        self.stdout.write(f'Testing with photo {test_photo.id}: {test_photo.title}')
        
        # Show photo info
        if test_photo.latitude and test_photo.longitude:
            self.stdout.write(f'Location: {test_photo.latitude}, {test_photo.longitude}')
        else:
            self.stdout.write('No location data')

        # Test FAISS
        self.stdout.write(f'\n🚀 Testing FAISS (limit={limit}, threshold={threshold})')
        start_time = time.time()
        
        try:
            faiss_results = find_similar_photos_visual_location(
                test_photo,
                limit=limit,
                threshold=threshold,
                method="cosine",
                use_faiss=True
            )
            faiss_time = time.time() - start_time
            
            self.stdout.write(f'✅ FAISS completed in {faiss_time:.3f}s')
            self.stdout.write(f'Found {len(faiss_results)} similar photos')
            
            # Show top results
            for i, result in enumerate(faiss_results[:5], 1):
                photo = result['photo']
                visual = result['visual']
                location = result['location']
                final = result['final']
                self.stdout.write(f'  {i}. Photo {photo.id}: visual={visual:.3f}, location={location:.3f}, final={final:.3f}')
                
        except Exception as e:
            self.stdout.write(f'❌ FAISS failed: {e}')
            faiss_results = []
            faiss_time = 0

        # Test Brute Force
        self.stdout.write(f'\n🐌 Testing Brute Force (limit={limit}, threshold={threshold})')
        start_time = time.time()
        
        try:
            brute_results = find_similar_photos_visual_location(
                test_photo,
                limit=limit,
                threshold=threshold,
                method="cosine",
                use_faiss=False
            )
            brute_time = time.time() - start_time
            
            self.stdout.write(f'✅ Brute Force completed in {brute_time:.3f}s')
            self.stdout.write(f'Found {len(brute_results)} similar photos')
            
            # Show top results
            for i, result in enumerate(brute_results[:5], 1):
                photo = result['photo']
                visual = result['visual']
                location = result['location']
                final = result['final']
                self.stdout.write(f'  {i}. Photo {photo.id}: visual={visual:.3f}, location={location:.3f}, final={final:.3f}')
                
        except Exception as e:
            self.stdout.write(f'❌ Brute Force failed: {e}')
            brute_results = []
            brute_time = 0

        # Performance comparison
        self.stdout.write(f'\n📊 Performance Comparison')
        self.stdout.write('-' * 30)
        
        if faiss_time > 0 and brute_time > 0:
            speedup = brute_time / faiss_time
            self.stdout.write(f'FAISS time: {faiss_time:.3f}s')
            self.stdout.write(f'Brute Force time: {brute_time:.3f}s')
            self.stdout.write(f'Speedup: {speedup:.1f}x faster')
        else:
            self.stdout.write('Could not compare performance due to errors')

        # Results comparison
        self.stdout.write(f'\n🎯 Results Comparison')
        self.stdout.write('-' * 30)
        
        if faiss_results and brute_results:
            faiss_ids = {result['photo'].id for result in faiss_results}
            brute_ids = {result['photo'].id for result in brute_results}
            
            common = faiss_ids & brute_ids
            faiss_only = faiss_ids - brute_ids
            brute_only = brute_ids - faiss_ids
            
            self.stdout.write(f'Common results: {len(common)}')
            self.stdout.write(f'FAISS only: {len(faiss_only)}')
            self.stdout.write(f'Brute Force only: {len(brute_only)}')
            
            if common:
                self.stdout.write(f'Common photo IDs: {sorted(list(common))}')
            if faiss_only:
                self.stdout.write(f'FAISS only IDs: {sorted(list(faiss_only))}')
            if brute_only:
                self.stdout.write(f'Brute Force only IDs: {sorted(list(brute_only))}')
        else:
            self.stdout.write('Could not compare results due to errors')

        self.stdout.write(f'\n{self.style.SUCCESS("FAISS performance test completed!")}')
