# users/management/commands/setup_recommendations.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.tasks import calculate_user_recommendations_task, cleanup_old_recommendations, update_recommendation_cache
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Setup automatic user recommendation tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if tasks already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write('Setting up automatic recommendation tasks...')
        
        # Create interval schedules
        daily_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        
        hourly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )
        
        weekly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=7,
            period=IntervalSchedule.DAYS,
        )
        
        # Task 1: Daily full recommendation calculation
        task_name = 'daily_full_recommendations'
        if force or not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'task': 'users.tasks.calculate_user_recommendations_task',
                    'interval': daily_schedule,
                    'args': '[]',
                    'kwargs': '{}',
                    'enabled': True,
                    'description': 'Calculate recommendations for all users daily',
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created/Updated task: {task_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Task already exists: {task_name}')
            )
        
        # Task 2: Hourly cache update for active users
        task_name = 'hourly_cache_update'
        if force or not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'task': 'users.tasks.update_recommendation_cache',
                    'interval': hourly_schedule,
                    'args': '[]',
                    'kwargs': '{}',
                    'enabled': True,
                    'description': 'Update recommendation cache for active users',
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created/Updated task: {task_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Task already exists: {task_name}')
            )
        
        # Task 3: Weekly cleanup of old recommendations
        task_name = 'weekly_cleanup'
        if force or not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    'task': 'users.tasks.cleanup_old_recommendations',
                    'interval': weekly_schedule,
                    'args': '[]',
                    'kwargs': '{}',
                    'enabled': True,
                    'description': 'Clean up old recommendation entries',
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created/Updated task: {task_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Task already exists: {task_name}')
            )
        
        # Trigger initial calculation for all users
        self.stdout.write('Triggering initial recommendation calculation...')
        try:
            calculate_user_recommendations_task.delay()
            self.stdout.write(
                self.style.SUCCESS('✓ Initial calculation started in background')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to start initial calculation: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Recommendation system setup complete!')
        )
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Start Celery worker: celery -A shuttrly worker -l info')
        self.stdout.write('2. Start Celery beat: celery -A shuttrly beat -l info')
        self.stdout.write('3. Check recommendations in the home page sidebar')
