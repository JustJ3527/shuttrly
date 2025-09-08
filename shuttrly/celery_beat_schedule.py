# Celery Beat configuration for periodic tasks
from celery.schedules import crontab

# Periodic tasks schedule
CELERY_BEAT_SCHEDULE = {
    # Update recommendations every 30 minutes
    'periodic-recommendations-update': {
        'task': 'users.tasks.periodic_recommendations_update',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    
    # Clean up old recommendations every hour
    'cleanup-old-recommendations': {
        'task': 'users.tasks.cleanup_old_recommendations',
        'schedule': crontab(minute=0),  # Every hour
    },
}
