# users/management/commands/auto_recommendations.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.utilsFolder.recommendations import build_user_recommendations
from users.models import UserRecommendation, UserRelationship
import time
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Run automatic recommendation updates (simple version without Celery)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,  # 1 hour
            help='Update interval in seconds (default: 3600 = 1 hour)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(f'Starting automatic recommendation updates (interval: {interval}s)')
        
        if run_once:
            self.update_recommendations()
            return
        
        # Continuous loop
        try:
            while True:
                self.update_recommendations()
                self.stdout.write(f'Waiting {interval} seconds until next update...')
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Stopped automatic updates'))

    def update_recommendations(self):
        """Update recommendations if needed"""
        try:
            # Check if we need to update (e.g., new relationships since last update)
            last_recommendation = UserRecommendation.objects.order_by('-updated_at').first()
            last_relationship = UserRelationship.objects.order_by('-created_at').first()
            
            # Update if no recommendations exist or if new relationships were added
            if not last_recommendation or (last_relationship and last_relationship.created_at > last_recommendation.updated_at):
                self.stdout.write('Updating recommendations...')
                build_user_recommendations()
                self.stdout.write(self.style.SUCCESS('✓ Recommendations updated successfully'))
            else:
                self.stdout.write('No update needed - recommendations are up to date')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error updating recommendations: {e}'))
