"""
Django management command to toggle photo similarity in recommendations.

This command allows temporarily disabling photo similarity calculations
to improve performance or avoid CLIP model loading issues.

Usage:
    python manage.py toggle_photo_similarity --disable
    python manage.py toggle_photo_similarity --enable
    python manage.py toggle_photo_similarity --status
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Toggle photo similarity calculations in user recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable photo similarity calculations'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable photo similarity calculations'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current status of photo similarity'
        )

    def handle(self, *args, **options):
        enable = options['enable']
        disable = options['disable']
        status = options['status']

        if enable and disable:
            self.stdout.write(
                self.style.ERROR('Cannot use both --enable and --disable')
            )
            return

        if not enable and not disable and not status:
            # Show status by default
            status = True

        cache_key = 'photo_similarity_enabled'

        if enable:
            cache.set(cache_key, True, timeout=None)  # No expiration
            self.stdout.write(
                self.style.SUCCESS('✅ Photo similarity calculations ENABLED')
            )
            self.stdout.write(
                'Photo similarity will be included in user recommendations.'
            )

        elif disable:
            cache.set(cache_key, False, timeout=None)  # No expiration
            self.stdout.write(
                self.style.WARNING('⚠️ Photo similarity calculations DISABLED')
            )
            self.stdout.write(
                'Photo similarity will be skipped in user recommendations.'
            )
            self.stdout.write(
                'This can improve performance but may reduce recommendation quality.'
            )

        if status:
            is_enabled = cache.get(cache_key, True)  # Default to enabled
            if is_enabled:
                self.stdout.write(
                    self.style.SUCCESS('✅ Photo similarity is currently ENABLED')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Photo similarity is currently DISABLED')
                )

            # Show additional info
            self.stdout.write('\nTo change status:')
            self.stdout.write('  Enable:  python manage.py toggle_photo_similarity --enable')
            self.stdout.write('  Disable: python manage.py toggle_photo_similarity --disable')
