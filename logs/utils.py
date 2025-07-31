from django.utils.timezone import now
from pathlib import Path
import json
from django.conf import settings


def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


import json
from django.utils import timezone
from pathlib import Path
from django.conf import settings
import uuid

def log_user_action_json(user, action, request=None, extra_info=None, changes=None):

    log_dir = Path(settings.BASE_DIR) / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'user_logs.json'

    # Get IP and user-agent from request if available
    ip_address = None
    user_agent = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT')

    # Compose structured extra_info
    structured_extra_info = {}
    if ip_address:
        structured_extra_info['ip_address'] = ip_address
    if user_agent:
        structured_extra_info['user_agent'] = user_agent
    if changes:
        structured_extra_info['changes'] = changes
    elif extra_info:
        # If no changes dict but extra_info string given, put it under 'info'
        structured_extra_info['info'] = extra_info

    log_entry = {
        'log_id': str(uuid.uuid4()),
        'user': user.username if user else 'anonymous',
        'user_id': user.pk if user else None,
        'action': action,
        'timestamp': timezone.now().isoformat(),
        'extra_info': structured_extra_info,
    }

    # Load existing logs
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)