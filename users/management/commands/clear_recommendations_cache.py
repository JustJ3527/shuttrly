"""
Django management command to clear recommendations cache.

This command helps clean up stale cache entries that might contain
references to deleted users or outdated recommendations.

Usage:
    python manage.py clear_recommendations_cache
    python manage.py clear_recommendations_cache --user-id 123
    python manage.py clear_recommendations_cache --all
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Clear recommendations cache for all users or specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Clear cache for specific user ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all recommendations cache (including photo similarity)'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        clear_all = options['all']

        if user_id:
            # Clear cache for specific user
            self._clear_user_cache(user_id)
            
        elif clear_all:
            # Clear all recommendation-related cache
            self._clear_all_cache()
            
        else:
            # Clear cache for all existing users
            self._clear_all_user_caches()

    def _clear_user_cache(self, user_id):
        """Clear cache for a specific user"""
        try:
            user = User.objects.get(id=user_id)
            cache_key = f"user_recommendations_{user_id}"
            
            if cache.delete(cache_key):
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cleared cache for user {user.username} (ID: {user_id})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ No cache found for user {user.username} (ID: {user_id})')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User with ID {user_id} not found')
            )

    def _clear_all_user_caches(self):
        """Clear recommendations cache for all existing users"""
        users = User.objects.filter(is_active=True)
        cleared_count = 0
        
        self.stdout.write(f'🔄 Clearing cache for {users.count()} users...')
        
        for user in users:
            cache_key = f"user_recommendations_{user.id}"
            if cache.delete(cache_key):
                cleared_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Cleared cache for {cleared_count} users')
        )

    def _clear_all_cache(self):
        """Clear all recommendation-related cache entries"""
        cleared_count = 0
        
        # Get all active users to build cache keys
        users = User.objects.filter(is_active=True)
        
        self.stdout.write('🔄 Clearing all recommendation caches...')
        
        # Clear user recommendation caches
        for user in users:
            cache_key = f"user_recommendations_{user.id}"
            if cache.delete(cache_key):
                cleared_count += 1
        
        # Clear photo similarity caches (these use different pattern)
        # We can't easily enumerate all photo similarity cache keys,
        # so we'll clear the global toggle and let them expire naturally
        photo_sim_cleared = cache.delete('photo_similarity_enabled')
        if photo_sim_cleared:
            cleared_count += 1
            self.stdout.write('🔄 Cleared photo similarity toggle cache')
        
        # Try to clear some common photo similarity cache patterns
        # This is a best-effort cleanup
        similarity_cleared = 0
        for user1 in users[:50]:  # Limit to first 50 users to avoid too many operations
            for user2 in users[:50]:
                if user1.id != user2.id:
                    cache_key = f"photo_similarity_{min(user1.id, user2.id)}_{max(user1.id, user2.id)}"
                    if cache.delete(cache_key):
                        similarity_cleared += 1
        
        if similarity_cleared > 0:
            self.stdout.write(f'🔄 Cleared {similarity_cleared} photo similarity cache entries')
            cleared_count += similarity_cleared
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Cleared {cleared_count} total cache entries')
        )
        
        # Additional cleanup suggestions
        self.stdout.write(
            self.style.WARNING(
                '⚠️ Note: Some photo similarity caches may remain. '
                'They will expire naturally or be updated on next calculation.'
            )
        )
