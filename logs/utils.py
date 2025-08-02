import json
import uuid
from pathlib import Path
from django.utils import timezone
from django.conf import settings


def log_user_action_json(user, action, request=None, extra_info=None, changes=None):
    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'user_logs.json'

    # Récupération des infos requête
    ip_address = None
    user_agent = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

    structured_extra_info = {}
    if ip_address:
        structured_extra_info['ip_address'] = ip_address
    if user_agent:
        structured_extra_info['user_agent'] = user_agent
    if changes:
        structured_extra_info['changes'] = json.dumps(changes, ensure_ascii=False)
    elif extra_info:
        structured_extra_info['info'] = extra_info

    log_entry = {
        'log_id': str(uuid.uuid4()),
        'user': user.username if user else 'anonymous',
        'user_id': user.pk if user else None,
        'action': action,
        'timestamp': timezone.now().isoformat(),
        'extra_info': structured_extra_info,
        'restored': False,
    }

    # Convertir l'entrée en JSON formaté (avec indentation)
    log_json = json.dumps(log_entry, ensure_ascii=False, indent=2)

    # Si le fichier n'existe pas, créer avec une liste contenant l'entrée
    if not log_file.exists():
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            f.write(log_json)
            f.write('\n]')
    else:
        # Ouvrir en lecture+écriture, aller juste avant le dernier caractère (])
        with open(log_file, 'rb+') as f:
            f.seek(-1, 2)  # Aller à 1 caractère avant la fin
            last_char = f.read(1)

            if last_char == b']':
                f.seek(-1, 2)  # Revenir avant le ]
                f.write(b',\n')  # Ajouter une virgule
                f.write(log_json.encode('utf-8'))  # Ajouter la nouvelle entrée
                f.write(b'\n]')  # Fermer le tableau
            else:
                raise ValueError("Fichier user_logs.json corrompu : ne se termine pas par ']'")