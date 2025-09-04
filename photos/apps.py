from django.apps import AppConfig


class PhotosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "photos"
    
    def ready(self):
        """Import signals when the app is ready"""
        import photos.faiss_signals