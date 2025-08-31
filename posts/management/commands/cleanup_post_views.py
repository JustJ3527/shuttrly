from django.core.management.base import BaseCommand
from posts.models import Post


class Command(BaseCommand):
    help = 'Clean up old post view records and sync view counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep view records (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would clean up views older than {days} days'
                )
            )
        
        # Get count of old views
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_views_count = Post.objects.first().view_records.filter(
            viewed_at__lt=cutoff_date
        ).count() if Post.objects.exists() else 0
        
        if old_views_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No old view records to clean up')
            )
            return
        
        if dry_run:
            self.stdout.write(
                f'Would delete {old_views_count} old view records'
            )
            return
        
        # Actually clean up old views
        deleted_count = Post.cleanup_old_views(days_to_keep=days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {deleted_count} old view records'
            )
        )
        
        # Show some stats
        total_posts = Post.objects.count()
        total_views = sum(post.views_count for post in Post.objects.all())
        
        self.stdout.write(
            f'Total posts: {total_posts}'
        )
        self.stdout.write(
            f'Total views across all posts: {total_views}'
        )
