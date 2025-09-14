from django.core.management.base import BaseCommand
from users.utils import sync_follow_request_notifications


class Command(BaseCommand):
    help = 'Synchronize follow request notifications with their current status'

    def handle(self, *args, **options):
        self.stdout.write('Starting notification synchronization...')
        
        try:
            sync_follow_request_notifications()
            self.stdout.write(
                self.style.SUCCESS('Successfully synchronized follow request notifications')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error synchronizing notifications: {str(e)}')
            )
