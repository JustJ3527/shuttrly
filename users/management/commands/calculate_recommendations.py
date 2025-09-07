# users/management/commands/calculate_recommendations.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.utilsFolder.recommendations import build_user_recommendations, get_recommendations_for_display
from users.models import UserRecommendation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Calculate user recommendations directly (without Celery)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Calculate recommendations for specific user only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation even if recommendations exist',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        force = options.get('force', False)
        
        if user_id:
            # Calculate for specific user
            self.stdout.write(f'Calculating recommendations for user {user_id}...')
            try:
                user = User.objects.get(id=user_id)
                
                # Clear existing recommendations for this user if force
                if force:
                    UserRecommendation.objects.filter(user=user).delete()
                    self.stdout.write(f'Cleared existing recommendations for user {user_id}')
                
                # Calculate recommendations
                from users.tasks import _calculate_single_user_recommendations
                recommendations = _calculate_single_user_recommendations(user)
                
                if recommendations:
                    # Save to database
                    for rec_data in recommendations:
                        UserRecommendation.objects.update_or_create(
                            user=user,
                            recommended_user_id=rec_data['id'],
                            defaults={'score': rec_data['score']}
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created {len(recommendations)} recommendations for user {user_id}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ No recommendations generated for user {user_id}')
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ User {user_id} not found')
                )
        else:
            # Calculate for all users
            self.stdout.write('Calculating recommendations for all users...')
            
            # Clear existing recommendations if force
            if force:
                UserRecommendation.objects.all().delete()
                self.stdout.write('Cleared all existing recommendations')
            
            # Calculate recommendations for all users
            try:
                build_user_recommendations()
                total_recommendations = UserRecommendation.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created {total_recommendations} recommendations for all users')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error calculating recommendations: {e}')
                )
        
        # Show some sample recommendations
        self.stdout.write('\nSample recommendations:')
        sample_recommendations = UserRecommendation.objects.select_related('user', 'recommended_user')[:5]
        for rec in sample_recommendations:
            self.stdout.write(
                f'  {rec.user.username} -> {rec.recommended_user.username} (score: {rec.score:.3f})'
            )
