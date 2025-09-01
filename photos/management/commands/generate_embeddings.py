from django.core.management.base import BaseCommand
from django.db import transaction
from photos.models import Photo
from photos.utils import get_image_embedding
import os


class Command(BaseCommand):
    help = 'Generate embeddings for photos that don\'t have them yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of photos to process (default: 10)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate embeddings for photos that already have them'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Only process photos for a specific user'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        user_id = options['user_id']

        # Get photos to process
        if force:
            photos = Photo.objects.all()
            self.stdout.write(f"Force mode: will regenerate embeddings for all photos")
        else:
            photos = Photo.objects.filter(embedding__isnull=True)
            self.stdout.write(f"Normal mode: will generate embeddings for photos without them")

        if user_id:
            photos = photos.filter(user_id=user_id)
            self.stdout.write(f"Filtering by user ID: {user_id}")

        photos = photos[:limit]
        total_photos = photos.count()

        if total_photos == 0:
            self.stdout.write(
                self.style.WARNING('No photos found to process')
            )
            return

        self.stdout.write(f"Processing {total_photos} photos...")

        success_count = 0
        error_count = 0

        for i, photo in enumerate(photos, 1):
            try:
                self.stdout.write(f"[{i}/{total_photos}] Processing photo {photo.id}: {photo.title}")

                # Check if file exists
                if not os.path.exists(photo.original_file.path):
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ File not found: {photo.original_file.path}")
                    )
                    error_count += 1
                    continue

                # Generate embedding
                embedding = get_image_embedding(photo.original_file.path)
                
                if embedding:
                    with transaction.atomic():
                        photo.embedding = embedding
                        photo.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Success! Generated embedding with {len(embedding)} dimensions")
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Failed to generate embedding")
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error processing photo {photo.id}: {str(e)}")
                )
                error_count += 1

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("SUMMARY:")
        self.stdout.write(f"  Total processed: {total_photos}")
        self.stdout.write(f"  Successful: {success_count}")
        self.stdout.write(f"  Errors: {error_count}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Successfully generated {success_count} embeddings!")
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  {error_count} photos failed to process")
            )
