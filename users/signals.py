from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

@receiver(user_logged_in)
def update_last_login_ip(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    if ip != user.last_login_ip:  # éviter un save inutile si identique
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])
def user_logged_in_handler(sender, request, user, **kwargs):
  user.is_online = True
  user.save()


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    user.is_online = False
    user.save()

# from django.db.models.signals import pre_save
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
# from .utils import schedule_profile_picture_deletion

# User = get_user_model()

# @receiver(pre_save, sender=User)
# def handle_profile_picture_change(sender, instance, **kwargs):
#     """
#     Signal déclenché avant la sauvegarde d'un utilisateur
#     """
#     if instance.pk:  # Si l'utilisateur existe déjà
#         try:
#             old_user = User.objects.get(pk=instance.pk)
#             # Vérifier si la photo de profil a changé
#             if (old_user.profile_picture and 
#                 old_user.profile_picture != instance.profile_picture):
#                 schedule_profile_picture_deletion(
#                     old_user.profile_picture.name, 
#                     days=30
#                 )
#         except User.DoesNotExist:
#             pass
