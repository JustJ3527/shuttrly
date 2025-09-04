"""
Django management command for FAISS index management.

This command provides utilities to build, rebuild, and manage the FAISS index
for photo similarity search.
"""

from django.core.management.base import BaseCommand, CommandError
from photos.models import Photo
from photos.faiss_index import build_faiss_index, get_faiss_stats, faiss_index
import time


class Command(BaseCommand):
    help = 'Manage FAISS index for photo similarity search'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['build', 'rebuild', 'stats', 'clear'],
            help='Action to perform on the FAISS index'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rebuild even if index exists'
        )

    def handle(self, *args, **options):
        action = options['action']
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS(f'FAISS Index Management - Action: {action}'))

        if action == 'build':
            self.build_index(force)
        elif action == 'rebuild':
            self.rebuild_index()
        elif action == 'stats':
            self.show_stats()
        elif action == 'clear':
            self.clear_index()

    def build_index(self, force=False):
        """Build FAISS index from database photos"""
        self.stdout.write('Building FAISS index...')
        
        # Check if photos with embeddings exist
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        )
        
        if not photos_with_embeddings.exists():
            raise CommandError('No photos with embeddings found in database')
        
        self.stdout.write(f'Found {photos_with_embeddings.count()} photos with embeddings')
        
        # Build index
        start_time = time.time()
        success = build_faiss_index(force_rebuild=force)
        build_time = time.time() - start_time
        
        if success:
            stats = get_faiss_stats()
            self.stdout.write(
                self.style.SUCCESS(
                    f'FAISS index built successfully in {build_time:.2f}s'
                )
            )
            self.stdout.write(f'Index contains {stats["total_photos"]} photos')
        else:
            raise CommandError('Failed to build FAISS index')

    def rebuild_index(self):
        """Rebuild FAISS index from scratch"""
        self.stdout.write('Rebuilding FAISS index...')
        
        # Check if photos with embeddings exist
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        )
        
        if not photos_with_embeddings.exists():
            raise CommandError('No photos with embeddings found in database')
        
        self.stdout.write(f'Found {photos_with_embeddings.count()} photos with embeddings')
        
        # Rebuild index
        start_time = time.time()
        success = build_faiss_index(force_rebuild=True)
        build_time = time.time() - start_time
        
        if success:
            stats = get_faiss_stats()
            self.stdout.write(
                self.style.SUCCESS(
                    f'FAISS index rebuilt successfully in {build_time:.2f}s'
                )
            )
            self.stdout.write(f'Index contains {stats["total_photos"]} photos')
        else:
            raise CommandError('Failed to rebuild FAISS index')

    def show_stats(self):
        """Show FAISS index statistics"""
        stats = get_faiss_stats()
        
        self.stdout.write('\n=== FAISS Index Statistics ===')
        self.stdout.write(f'Total photos in index: {stats["total_photos"]}')
        self.stdout.write(f'Index size: {stats["index_size"]}')
        self.stdout.write(f'Embedding dimension: {stats["dimension"]}')
        self.stdout.write(f'Index path: {stats["index_path"]}')
        self.stdout.write(f'Index loaded: {stats["is_loaded"]}')
        
        # Show database stats for comparison
        total_photos = Photo.objects.count()
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        ).count()
        
        self.stdout.write('\n=== Database Statistics ===')
        self.stdout.write(f'Total photos in database: {total_photos}')
        self.stdout.write(f'Photos with embeddings: {photos_with_embeddings}')
        
        if stats["total_photos"] != photos_with_embeddings:
            self.stdout.write(
                self.style.WARNING(
                    'WARNING: Index and database are out of sync!'
                )
            )
            self.stdout.write('Consider running: python manage.py manage_faiss_index rebuild')

    def clear_index(self):
        """Clear FAISS index"""
        self.stdout.write('Clearing FAISS index...')
        
        try:
            # Clear the index
            faiss_index.index = None
            faiss_index.photo_ids = []
            faiss_index.id_to_index = {}
            
            # Save empty index
            faiss_index._save_index()
            
            self.stdout.write(
                self.style.SUCCESS('FAISS index cleared successfully')
            )
        except Exception as e:
            raise CommandError(f'Failed to clear FAISS index: {e}')
