from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from adminpanel.forms import CustomUserAdminForm
from users.models import CustomUser
from django.contrib.auth.models import Group
import json
from pathlib import Path
from django.conf import settings

import uuid

@staff_member_required
def admin_dashboard_view(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'adminpanel/dashboard.html', {'users': users})

@staff_member_required
@require_http_methods(["GET", "POST"])
def edit_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = CustomUserAdminForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"{user.username} has been updated.")
            return redirect('admin_dashboard')
    else:
        form = CustomUserAdminForm(instance=user)

    return render(request, 'adminpanel/edit_user.html', {'form': form, 'target_user': user})

@staff_member_required
@require_http_methods(["POST"])
def delete_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_superuser:
        messages.error(request, "You cannot delete a superuser from here.")
    else:
        user.delete()
        messages.success(request, "User deleted.")
    return redirect('admin_dashboard')

@staff_member_required
def group_dashboard_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users = group.user_set.all()
    return render(request, 'adminpanel/group_users.html', {'group': group, 'users': users})

from logs.models import UserLog

@staff_member_required
def user_logs_view(request):
    logs_path = Path(settings.BASE_DIR) / 'logs' / 'user_logs.json'
    if not logs_path.exists():
        logs = []
    else:
        with open(logs_path, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    # Optionnel : trier logs par timestamp décroissant si nécessaire
    logs = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return render(request, 'adminpanel/user_logs.html', {'logs': logs})

import json
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from pathlib import Path
from django.utils import timezone

@staff_member_required
@require_http_methods(["POST"])
def restore_log_action_view(request):
    log_index = request.POST.get('log_index')
    if log_index is None:
        messages.error(request, "Log index not provided.")
        return redirect('adminpanel:user_logs')

    try:
        log_index = int(log_index)
    except ValueError:
        messages.error(request, "Invalid log index.")
        return redirect('adminpanel:user_logs')

    logs_path = Path(settings.BASE_DIR) / 'logs' / 'user_logs.json'
    if not logs_path.exists():
        messages.error(request, "Logs file not found.")
        return redirect('adminpanel:user_logs')

    with open(logs_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)

    if log_index < 0 or log_index >= len(logs):
        messages.error(request, "Log index out of range.")
        return redirect('adminpanel:user_logs')

    log_entry = logs[log_index]

    if log_entry['action'] == 'update_profile':
        from users.models import CustomUser
        user_id = log_entry['user_id']
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found for this log entry.")
            return redirect('adminpanel:user_logs')

        changes = log_entry.get('extra_info', {}).get('info', {}).get('changes', {})
        if not changes:
            messages.error(request, "No changes found to restore.")
            return redirect('adminpanel:user_logs')

        # Appliquer la restauration : remettre les anciennes valeurs
        for field, values in changes.items():
            old_value = values[0]  # ancienne valeur
            setattr(user, field, old_value)
        user.save()

        messages.success(request, f"User '{user.username}' profile restored to previous state from log.")

        # Récupérer IP et User-Agent du restaurateur (celui qui fait la requête)
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')

        # Construire un nouveau log détaillé de la restauration
        new_log = {
            "log_id": str(uuid.uuid4()),
            "user": request.user.username,
            "user_id": request.user.id,
            "action": "restore_action",
            "timestamp": timezone.now().isoformat(),
            "extra_info": {
                "ip_address": ip,
                "user_agent": user_agent,
                "restored_log_index": log_index,
                "restored_from_log_id":log_entry.get('log_id'),
                "restored_log_user": log_entry.get('user', ''),
                "restored_log_user_id": user_id,
                "restored_action": log_entry.get('action', ''),
                "restored_changes": changes,
                "note": f"Restored profile for user '{user.username}' to previous state."
            }
        }
        logs.append(new_log)

        # Sauvegarder dans le fichier JSON sans supprimer les logs précédents
        with open(logs_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    else:
        messages.warning(request, "Restoration not supported for this action type.")

    return redirect('adminpanel:user_logs')