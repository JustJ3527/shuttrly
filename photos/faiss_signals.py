"""
Django signals for automatic FAISS index management.

This module handles automatic updates to the FAISS index when photos are
created, updated, or deleted. It ensures the index stays in sync with
the database.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Photo
from .faiss_index import update_faiss_index, remove_from_faiss_index
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Photo)
def update_faiss_on_photo_save(sender, instance, created, **kwargs):
    """
    Update FAISS index when a photo is saved.
    
    Args:
        sender: The model class (Photo)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Only update if the photo has an embedding
        if instance.embedding:
            success = update_faiss_index(instance)
            if success:
                action = "added to" if created else "updated in"
                logger.info(f"Photo {instance.id} {action} FAISS index")
            else:
                logger.warning(f"Failed to update FAISS index for photo {instance.id}")
        else:
            # If photo has no embedding, remove it from index if it exists
            remove_from_faiss_index(instance.id)
            logger.info(f"Photo {instance.id} removed from FAISS index (no embedding)")
            
    except Exception as e:
        logger.error(f"Error updating FAISS index for photo {instance.id}: {e}")


@receiver(post_delete, sender=Photo)
def remove_from_faiss_on_photo_delete(sender, instance, **kwargs):
    """
    Remove photo from FAISS index when it's deleted.
    
    Args:
        sender: The model class (Photo)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    try:
        success = remove_from_faiss_index(instance.id)
        if success:
            logger.info(f"Photo {instance.id} removed from FAISS index")
        else:
            logger.warning(f"Failed to remove photo {instance.id} from FAISS index")
            
    except Exception as e:
        logger.error(f"Error removing photo {instance.id} from FAISS index: {e}")
