from django.core.mail import send_mail
from .models import UserLog
import os
from django.conf import settings
from datetime import datetime

def send_2fa_email_code(user, code):
    send_mail(
        "Code de vérification - Connexion",
        f"Bonjour,\n\nVotre code de vérification est : {code}",
        "no-reply@tonsite.com",
        [user.email]
    )

def get_client_ip(request):
    """Récupère l'adresse IP du client depuis l'objet request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ---------====== LOGS ======--------- #

def log_user_action(user, action, request=None, extra_info=""):
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    UserLog.objects.create(user=user, action=action, ip_address=ip, extra_info=extra_info)

def log_user_profile_changes(user, old_data, new_data, request):
    print("LOG USER PROFILE CHANGES CALLED")  # Debug print
    changes = []

    # Check for differences in editable fields
    for field in ['frist_name', 'last_name', 'email', 'username', 'profile_picture']:
        old_value = getattr(old_data, field, None)
        new_value = getattr(new_data, field, None)

        if field == 'profile_picture':
            old_value = old_value.url if old_value else None
            new_value = new_value.url if new_value else None

        if old_value != new_value:
            changes.append(f"{field} changed from '{old_value}' to '{new_value}'")
    
    if changes:
        # Log in database
        UserLog.objects.create(
            user=user,
            action='update_profile',
            ip_address=request.META.get('REMOTE_ADDR'),
            extra_info="\n".join(changes)
        )

        # Log in file
        log_line = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
            f"User '{user.username}' updated profile from IP {request.META.get('REMOTE_ADDR')}:\n" +
            "\n".join(f" - {c}" for c in changes) + "\n\n"
        )

        log_path = os.path.join(settings.BASE_DIR, 'logs')
        print("Log folder:", log_path)
        os.makedirs(log_path, exist_ok=True)
        file_path = os.path.join(log_path, 'user_logs.txt')
        print("Log file path:", file_path)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(log_line)