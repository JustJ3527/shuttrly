# === Django imports ===
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.conf import settings

# === Python stdlib ===
import json
import uuid
from pathlib import Path
from datetime import datetime

# === Models and forms ===
from users.models import CustomUser, PendingFileDeletion
from django.contrib.auth.models import Group
from adminpanel.forms import CustomUserAdminForm

# === Utils ===
from logs.utils import log_user_action_json
from users.utils import get_changes_dict, get_location_from_ip


# === Views ===


@staff_member_required
def admin_dashboard_view(request):
    users = CustomUser.objects.all().order_by("-date_joined")
    return render(request, "adminpanel/dashboard.html", {"users": users})


@staff_member_required
@require_http_methods(["GET", "POST"])
def edit_user_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        form = CustomUserAdminForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_data = CustomUser.objects.get(pk=user.pk)  # récupérer avant sauvegarde

            updated_user = form.save()

            ip = request.META.get("REMOTE_ADDR", "unknown")
            user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

            # Utiliser la fonction utilitaire pour détecter les changements
            changes_dict = get_changes_dict(old_data, updated_user, form.changed_data)

            log_user_action_json(
                user=request.user,
                action="admin_edit_user",
                request=request,
                extra_info={
                    "impacted_user_id": user.id,
                    "changes": changes_dict,
                },
            )

            messages.success(request, f"{user.username} has been updated.")
            return redirect("adminpanel:admin_dashboard")
    else:
        form = CustomUserAdminForm(instance=user)

    return render(
        request, "adminpanel/edit_user.html", {"form": form, "target_user": user}
    )


@staff_member_required
@require_http_methods(["POST"])
def delete_user_view(request, user_id):
    user_to_delete = get_object_or_404(CustomUser, id=user_id)

    if user_to_delete.is_superuser:
        messages.error(request, "You cannot delete a superuser from here.")
    else:
        if request.user.is_superuser:
            log_user_action_json(
                user=request.user,
                action="delete_user_account",
                request=request,
                extra_info={
                    "impacted_user_id": user_to_delete.id,
                },
            )
        user_to_delete.delete()
        messages.success(request, "User deleted.")

    return redirect("adminpanel:admin_dashboard")


@staff_member_required
def group_dashboard_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    users = group.user_set.all()
    return render(
        request, "adminpanel/group_users.html", {"group": group, "users": users}
    )


@staff_member_required
def user_logs_view(request):
    logs_path = Path(settings.BASE_DIR) / "logs" / "user_logs.json"
    logs = []

    if logs_path.exists():
        try:
            with open(logs_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            pass

    logs = sorted(logs, key=lambda x: x.get("timestamp", ""))
    return render(request, "adminpanel/user_logs.html", {"logs": logs})


@staff_member_required
@require_http_methods(["POST"])
def restore_log_action_view(request):
    def stringify_changes(changes):
        """
        Convertit les valeurs des changements en chaînes pour manipulation uniforme.
        """
        result = {}
        for key, values in changes.items():
            if isinstance(values, (list, tuple)) and len(values) >= 2:
                result[key] = [str(values[0]), str(values[1])]
            else:
                result[key] = [
                    str(v)
                    for v in (values if isinstance(values, (list, tuple)) else [values])
                ]
        return result

    # Récupérer l'index du log à restaurer depuis le POST
    log_index = request.POST.get("log_index")
    if log_index is None:
        messages.error(request, "Log index not provided.")
        return redirect("adminpanel:user_logs")

    try:
        log_index = int(log_index)
    except ValueError:
        messages.error(request, "Invalid log index.")
        return redirect("adminpanel:user_logs")

    # Chemin vers le fichier JSON des logs
    logs_path = Path(settings.BASE_DIR) / "logs" / "user_logs.json"
    if not logs_path.exists():
        messages.error(request, "Logs file not found.")
        return redirect("adminpanel:user_logs")

    # Lecture du fichier JSON
    try:
        with open(logs_path, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except json.JSONDecodeError:
        messages.error(request, "Could not read log file.")
        return redirect("adminpanel:user_logs")

    # Vérifier la validité de l'index
    if not (0 <= log_index < len(logs)):
        messages.error(request, "Log index out of range.")
        return redirect("adminpanel:user_logs")

    log_entry = logs[log_index]

    # Limiter la restauration aux actions 'update_profile'
    if log_entry.get("action") != "update_profile":
        messages.warning(request, "Only 'update_profile' logs can be restored.")
        return redirect("adminpanel:user_logs")

    extra_info = log_entry.get("extra_info", {})
    user_id = (
        log_entry.get("user_id")
        or extra_info.get("impacted_user_id")
        or extra_info.get("info", {}).get("impacted_user_id")
    )

    if not user_id:
        messages.error(request, "No user ID found in log entry.")
        return redirect("adminpanel:user_logs")

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, f"No user found with ID {user_id}.")
        return redirect("adminpanel:user_logs")

    changes = extra_info.get("info", {}).get("changes") or extra_info.get("changes")

    if not changes:
        messages.warning(request, "No changes found in log.")
        return redirect("adminpanel:user_logs")

    # Formater les changements
    changes = stringify_changes(changes)
    updated_fields = []
    restoration_details = {}

    # Appliquer les changements de restauration sur l'utilisateur
    for field, values in changes.items():
        if len(values) < 1:
            continue
        old_value = values[0]
        current_value = getattr(user, field, None)

        # Cas particulier pour la date
        if field == "date_of_birth" and isinstance(old_value, str):
            try:
                old_value = datetime.strptime(old_value, "%Y-%m-%d").date()
            except ValueError:
                continue

        if str(current_value) != str(old_value):
            setattr(user, field, old_value)
            updated_fields.append(field)
            restoration_details[field] = {
                "before_restoration": current_value,
                "after_restoration": old_value,
                "original_change": f"{old_value} → {current_value}",
            }

    # Gestion spécifique du champ profile_picture
    if "profile_picture" in changes:
        old_path = changes["profile_picture"][0]
        if old_path:
            rel_path = (
                old_path[len(settings.MEDIA_URL) :]
                if old_path.startswith(settings.MEDIA_URL)
                else old_path
            )
            from django.core.files.storage import default_storage

            if default_storage.exists(rel_path):
                user.profile_picture.name = rel_path
                updated_fields.append("profile_picture")
                restoration_details["profile_picture"] = {
                    "before_restoration": changes["profile_picture"][1],
                    "after_restoration": changes["profile_picture"][0],
                    "original_change": f"{changes['profile_picture'][0]} → {changes['profile_picture'][1]}",
                }
                PendingFileDeletion.objects.filter(file_path=rel_path).delete()
            else:
                messages.warning(
                    request, "Previous profile picture not found. Skipped restoring it."
                )

    # Sauvegarder l'utilisateur avec les champs modifiés
    user.save(update_fields=updated_fields)

    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    user_agent = request.META.get("HTTP_USER_AGENT", "unknown")
    location = get_location_from_ip(ip_address)

    # Ajouter un nouveau log de restauration dans le fichier JSON
    new_log = {
        "log_id": str(uuid.uuid4()),
        "user": request.user.username,
        "user_id": request.user.id,
        "action": "restore_profile_from_log",
        "timestamp": timezone.now().isoformat(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "location": {
            "city": location.get("city") if location else None,
            "region": location.get("region") if location else None,
            "country": location.get("country") if location else None,
        },
        "extra_info": {
            "restored_log_id": log_entry.get("log_id"),
            "restored_fields": updated_fields,
            "restoration_details": restoration_details,
            "impacted_user_id": user.id,
        },
    }
    logs.append(new_log)
    logs[log_index]["restored"] = True

    # Réécriture du fichier JSON
    with open(logs_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    # Préparer le message de succès avec détails des restaurations
    detail_list = "".join(
        f"<li><strong>{k}</strong>: '{v['before_restoration']}' → '<span class='text-success'>{v['after_restoration']}</span>'</li>"
        for k, v in restoration_details.items()
    )
    messages.success(
        request,
        mark_safe(
            f"""
        <div class='alert alert-success'>
            <h5><a href='#log-{log_entry.get('log_id')}'>Restoration complete</a></h5>
            <ul>{detail_list}</ul>
        </div>
    """
        ),
    )

    return redirect("adminpanel:user_logs")
