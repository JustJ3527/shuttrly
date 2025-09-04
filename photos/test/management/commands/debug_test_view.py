from django.core.management.base import BaseCommand
from photos.models import Photo
from photos.test_views import test_advanced_similarity_view
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug the test_advanced_similarity_view to check photo loading'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photo-id',
            type=int,
            default=None,
            help='Photo ID to test (default: first available)',
        )

    def handle(self, *args, **options):
        # Get a test user
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
            return
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/photos/test-advanced/')
        request.user = user
        
        # Get photos with embeddings
        photos_with_embeddings = Photo.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding=[]
        ).order_by('id')
        
        if not photos_with_embeddings.exists():
            self.stdout.write(self.style.ERROR('No photos with embeddings found.'))
            return
        
        self.stdout.write(f"Found {photos_with_embeddings.count()} photos with embeddings")
        
        # Test with specific photo ID or first photo
        photo_id = options['photo_id']
        if photo_id:
            try:
                test_photo = photos_with_embeddings.get(id=photo_id)
                self.stdout.write(f"Testing with photo ID: {photo_id}")
            except Photo.DoesNotExist:
                self.stdout.write(f"Photo ID {photo_id} not found. Using first available photo.")
                test_photo = photos_with_embeddings.first()
        else:
            test_photo = photos_with_embeddings.first()
        
        self.stdout.write(f"Test photo: ID {test_photo.id} - {test_photo.title}")
        
        # Test the view
        try:
            # Add photo_id to request
            if photo_id:
                request = factory.get(f'/photos/test-advanced/{photo_id}/')
            else:
                request = factory.get('/photos/test-advanced/')
            request.user = user
            
            # Call the view
            response = test_advanced_similarity_view(request, photo_id=photo_id)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('View rendered successfully!'))
                
                # Check context
                context = response.context_data
                if context:
                    self.stdout.write(f"Context data:")
                    self.stdout.write(f"  Current photo: {context.get('current_photo', 'None')}")
                    self.stdout.write(f"  Total photos with embeddings: {context.get('total_photos_with_embeddings', 'None')}")
                    self.stdout.write(f"  Photos with embeddings count: {context.get('photos_with_embeddings', 'None')}")
                    
                    # Check if photos_with_embeddings is in context
                    photos_in_context = context.get('photos_with_embeddings')
                    if photos_in_context:
                        self.stdout.write(f"  Photos in context: {photos_in_context.count() if hasattr(photos_in_context, 'count') else len(photos_in_context)}")
                        # Show first few
                        if hasattr(photos_in_context, 'count'):
                            for i, photo in enumerate(photos_in_context[:5]):
                                self.stdout.write(f"    {i+1}. ID: {photo.id} - {photo.title}")
                        else:
                            for i, photo in enumerate(photos_in_context[:5]):
                                self.stdout.write(f"    {i+1}. ID: {photo.id} - {photo.title}")
                    else:
                        self.stdout.write("  ❌ No photos_with_embeddings in context!")
            else:
                self.stdout.write(self.style.ERROR(f'View returned status code: {response.status_code}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing view: {e}'))
            import traceback
            traceback.print_exc()
        
        self.stdout.write(f"\n{self.style.SUCCESS('Debug test completed!')}")
