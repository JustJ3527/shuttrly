from django.core.mail import send_mail
# from .models import UserLog  # Supprimé : on n’utilise plus ce modèle
import os
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.files.storage import default_storage

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# users/utils.py - Version simplifiée et complète
from datetime import timedelta
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
import logging
import os
from django.conf import settings

# Configuration du logger
logger = logging.getLogger(__name__)

def schedule_profile_picture_deletion(file_path, seconds=None):
    try:
        # Import local pour éviter les imports circulaires
        from .models import PendingFileDeletion

        if seconds is None:
            seconds = getattr(settings, 'PROFILE_PICTURE_DELETION_DELAY_SECONDS', 86400)

        deletion_date = timezone.now() + timedelta(seconds=seconds)
        
        # Vérifier si le fichier n'est pas déjà programmé pour suppression
        existing = PendingFileDeletion.objects.filter(file_path=file_path).first()
        if not existing:
            PendingFileDeletion.objects.create(
                file_path=file_path,
                scheduled_deletion=deletion_date,
                reason='profile_picture_change'
            )
            print(f"✅ Scheduled deletion of {file_path} for {deletion_date}")
        else:
            print(f"⚠️ File {file_path} already scheduled for deletion on {existing.scheduled_deletion}")
            
    except Exception as e:
        print(f"❌ Error scheduling deletion for {file_path}: {str(e)}")
        logger.error(f"Error scheduling deletion for {file_path}: {str(e)}")


def is_file_still_in_use(file_path):
    """
    Vérifie si un fichier est encore utilisé par un utilisateur
    """
    try:
        User = get_user_model()
        
        # Vérifier si le fichier est encore utilisé comme profile_picture
        users_using_file = User.objects.filter(profile_picture=file_path)
        is_in_use = users_using_file.exists()
        
        if is_in_use:
            usernames = list(users_using_file.values_list('username', flat=True))
            print(f"⚠️ File {file_path} still in use by: {', '.join(usernames)}")
        
        return is_in_use
        
    except Exception as e:
        print(f"❌ Error checking if file is in use {file_path}: {str(e)}")
        logger.error(f"Error checking if file is in use {file_path}: {str(e)}")
        return True  # Par sécurité, on considère le fichier comme en cours d'utilisation


def cleanup_old_files():
    try:
        from .models import PendingFileDeletion
        
        now = timezone.now()
        
        files_to_delete = PendingFileDeletion.objects.filter(scheduled_deletion__lte=now)
        total_files = files_to_delete.count()
        
        print(f"🔍 Found {total_files} files to process...")
        
        deleted_count = 0
        skipped_count = 0
        error_count = 0
        
        for file_deletion in files_to_delete:
            try:
                print(f"📁 Processing: {file_deletion.file_path}")
                
                if default_storage.exists(file_deletion.file_path):
                    if not is_file_still_in_use(file_deletion.file_path):
                        # Supprimer le fichier
                        default_storage.delete(file_deletion.file_path)
                        print(f"✅ Deleted file: {file_deletion.file_path}")
                        
                        # Supprimer le dossier parent s'il est vide
                        file_full_path = os.path.join(settings.MEDIA_ROOT, file_deletion.file_path)
                        parent_dir = os.path.dirname(file_full_path)
                        
                        try:
                            if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                                print(f"🗑️ Deleted empty folder: {parent_dir}")
                        except Exception as e:
                            print(f"⚠️ Could not delete folder {parent_dir}: {e}")
                        
                        deleted_count += 1
                    else:
                        print(f"⚠️ File still in use, skipping: {file_deletion.file_path}")
                        skipped_count += 1
                        continue
                else:
                    print(f"ℹ️ File already deleted: {file_deletion.file_path}")
                
                file_deletion.delete()
                
            except Exception as e:
                print(f"❌ Error deleting file {file_deletion.file_path}: {str(e)}")
                error_count += 1
        
        print(f"📊 Summary: {deleted_count} deleted, {skipped_count} skipped, {error_count} errors")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Critical error in cleanup_old_files: {str(e)}")
        return 0

def get_storage_stats():
    """
    Obtient des statistiques sur le stockage des fichiers en attente
    """
    try:
        from .models import PendingFileDeletion
        from django.conf import settings
        
        pending_files = PendingFileDeletion.objects.all()
        total_size = 0
        existing_files = 0
        missing_files = 0
        
        for pending in pending_files:
            if default_storage.exists(pending.file_path):
                try:
                    # Calculer la taille du fichier
                    file_size = default_storage.size(pending.file_path)
                    total_size += file_size
                    existing_files += 1
                except:
                    missing_files += 1
            else:
                missing_files += 1
        
        # Convertir en MB
        total_size_mb = total_size / (1024 * 1024)
        
        stats = {
            'total_pending': pending_files.count(),
            'existing_files': existing_files,
            'missing_files': missing_files,
            'total_size_mb': round(total_size_mb, 2)
        }
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting storage stats: {str(e)}")
        logger.error(f"Error getting storage stats: {str(e)}")
        return None


def test_deletion_system():
    """
    Fonction de test pour vérifier que le système fonctionne
    """
    print("🧪 Testing deletion system...")
    
    # Créer un fichier de test
    test_file_path = "test/test_deletion.txt"
    
    try:
        # Créer le dossier de test
        test_dir = os.path.join(default_storage.location, 'test')
        os.makedirs(test_dir, exist_ok=True)
        
        # Créer un fichier de test
        full_path = os.path.join(test_dir, 'test_deletion.txt')
        with open(full_path, 'w') as f:
            f.write("This is a test file for deletion system")
        
        print(f"✅ Created test file: {test_file_path}")
        
        # Programmer sa suppression dans 1 minute pour test
        delay = getattr(settings, 'PROFILE_PICTURE_DELETION_DELAY_SECONDS', 86400)

        schedule_profile_picture_deletion(test_file_path, seconds=delay)  # 0 jours = immédiat
        
        print("✅ Scheduled test file for immediate deletion")
        
        # Tenter le nettoyage
        deleted = cleanup_old_files()
        
        if deleted > 0:
            print("✅ Deletion system is working correctly!")
        else:
            print("⚠️ No files were deleted during test")
            
        # Vérifier que le fichier a bien été supprimé
        if not default_storage.exists(test_file_path):
            print("✅ Test file was successfully deleted")
        else:
            print("❌ Test file still exists")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error(f"Test failed: {str(e)}")


# Fonction pour déboguer les problèmes
def debug_pending_deletions():
    """
    Affiche des informations de débogage sur les suppressions en attente
    """
    try:
        from .models import PendingFileDeletion
        
        print("🔍 DEBUG: Pending deletions")
        print("=" * 50)
        
        pending_files = PendingFileDeletion.objects.all().order_by('scheduled_deletion')
        
        if not pending_files.exists():
            print("ℹ️ No pending deletions found")
            return
        
        for i, pending in enumerate(pending_files, 1):
            print(f"\n📁 File #{i}:")
            print(f"   Path: {pending.file_path}")
            print(f"   Scheduled: {pending.scheduled_deletion}")
            print(f"   Created: {pending.created_at}")
            print(f"   Reason: {pending.reason}")
            print(f"   Exists: {'✅' if default_storage.exists(pending.file_path) else '❌'}")
            print(f"   In use: {'⚠️' if is_file_still_in_use(pending.file_path) else '✅'}")
        
        print(f"\n📊 Total: {pending_files.count()} files pending deletion")
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        logger.error(f"Debug failed: {str(e)}")


def get_changes_dict(old_obj, new_obj, changed_fields):
    changes = {}
    for field in changed_fields:
        old_val = getattr(old_obj, field, '')
        new_val = getattr(new_obj, field, '')

        # Si ce sont des fichiers (images etc.), récupérer leur URL
        if hasattr(old_val, 'url'):
            old_val = old_val.url
        if hasattr(new_val, 'url'):
            new_val = new_val.url

        changes[field] = [old_val, new_val]
    return changes

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', 'unknown')