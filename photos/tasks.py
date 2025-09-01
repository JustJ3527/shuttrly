from celery import shared_task
from .models import Photo
from .utils import get_image_embedding

@shared_task
def generate_embedding(photo_id):
    photo = Photo.objects.get(id=photo_id)
    embedding = get_image_embedding(photo.original_file.path)
    photo.embedding = embedding
    photo.save()
    return embedding