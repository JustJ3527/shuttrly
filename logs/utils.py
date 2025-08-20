import json
import uuid
import requests
from pathlib import Path
from django.utils import timezone
from django.conf import settings


def get_location_from_ip(ip_address):
    """
    Get approximate location info from IP address using ipinfo.io.
    Returns dict with city, region, country or empty dict on failure.
    """
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json/", timeout=2)
        data = response.json()
        return {
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
        }
    except Exception:
        return {}


def log_user_action_json(
    user,
    action,
    request=None,
    ip_address=None,
    user_agent=None,
    location=None,
    extra_info=None,
    restored=False,
):
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "user_logs.json"

    # Récupération IP & User-Agent depuis la requête si possible
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR")
        )
        user_agent = request.META.get("HTTP_USER_AGENT")

    # Localisation automatique si non fournie
    if not location and ip_address:
        location = get_location_from_ip(ip_address)

    # Construction de l'entrée de log
    log_entry = {
        "log_id": str(uuid.uuid4()),
        "user": user.username if user else "anonymous",
        "user_id": user.pk if user else None,
        "action": action,
        "timestamp": timezone.now().isoformat(),
        "ip_address": ip_address or None,
        "user_agent": user_agent or None,
        "location": {
            "city": location.get("city") if location else None,
            "region": location.get("region") if location else None,
            "country": location.get("country") if location else None,
        },
        "extra_info": extra_info or {},
        "restored": restored,
    }

    # Conversion en JSON formaté
    log_json = json.dumps(log_entry, ensure_ascii=False, indent=2)

    # Écriture dans le fichier JSON
    if not log_file.exists():
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("[\n")
            f.write(log_json)
            f.write("\n]")
    else:
        with open(log_file, "rb+") as f:
            f.seek(-1, 2)
            last_char = f.read(1)

            if last_char == b"]":
                f.seek(-1, 2)
                f.write(b",\n")
                f.write(log_json.encode("utf-8"))
                f.write(b"\n]")
            else:
                raise ValueError(
                    "Fichier user_logs.json corrompu : ne se termine pas par ']'"
                )


def log_photo_action_json(
    user,
    action,
    photo=None,
    request=None,
    ip_address=None,
    user_agent=None,
    location=None,
    extra_info=None,
):
    """
    Log photo-related actions to photo_logs.json file.

    Args:
        user: User performing the action
        action: Action type (upload, delete, edit, view, etc.)
        photo: Photo object (optional, for actions involving a specific photo)
        request: Django request object (optional, for IP and user agent)
        ip_address: IP address (optional, extracted from request if not provided)
        user_agent: User agent string (optional, extracted from request if not provided)
        location: Location dict (optional, auto-detected if not provided)
        extra_info: Additional information dict
    """
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "photo_logs.json"

    # Récupération IP & User-Agent depuis la requête si possible
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = (
            x_forwarded_for.split(",")[0].strip()
            if x_forwarded_for
            else request.META.get("REMOTE_ADDR")
        )
        user_agent = request.META.get("HTTP_USER_AGENT")

    # Localisation automatique si non fournie
    if not location and ip_address:
        location = get_location_from_ip(ip_address)

    # Construction de l'entrée de log
    log_entry = {
        "log_id": str(uuid.uuid4()),
        "user": user.username if user else "anonymous",
        "user_id": user.pk if user else None,
        "action": action,
        "timestamp": timezone.now().isoformat(),
        "ip_address": ip_address or None,
        "user_agent": user_agent or None,
        "location": {
            "city": location.get("city") if location else None,
            "region": location.get("region") if location else None,
            "country": location.get("country") if location else None,
        },
        "photo_info": (
            {
                "photo_id": photo.id if photo else None,
                "filename": photo.original_file.name.split("/")[-1] if photo else None,
                "file_size_mb": (
                    round(photo.file_size / (1024 * 1024), 2) if photo else None
                ),
                "file_extension": photo.file_extension if photo else None,
                "is_raw": photo.is_raw if photo else None,
                "dimensions": (
                    f"{photo.width}x{photo.height}"
                    if photo and photo.width and photo.height
                    else None
                ),
                "camera": (
                    f"{photo.camera_make} {photo.camera_model}".strip()
                    if photo and (photo.camera_make or photo.camera_model)
                    else None
                ),
            }
            if photo
            else None
        ),
        "extra_info": extra_info or {},
    }

    # Conversion en JSON formaté
    log_json = json.dumps(log_entry, ensure_ascii=False, indent=2)

    # Écriture dans le fichier JSON
    if not log_file.exists():
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("[\n")
            f.write(log_json)
            f.write("\n]")
    else:
        # Vérifier si le fichier est vide ou contient juste "[]"
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if content == "[]" or content == "":
                # Fichier vide, réécrire complètement
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("[\n")
                    f.write(log_json)
                    f.write("\n]")
            else:
                # Fichier avec contenu, ajouter à la fin
                with open(log_file, "rb+") as f:
                    f.seek(-1, 2)
                    last_char = f.read(1)

                    if last_char == b"]":
                        f.seek(-1, 2)
                        f.write(b",\n")
                        f.write(log_json.encode("utf-8"))
                        f.write(b"\n]")
                    else:
                        raise ValueError(
                            "Fichier photo_logs.json corrompu : ne se termine pas par ']'"
                        )
        except Exception as e:
            # En cas d'erreur, réécrire complètement le fichier
            print(f"Warning: Error reading photo_logs.json, recreating: {e}")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("[\n")
                f.write(log_json)
                f.write("\n]")


def log_photo_upload_json(
    user,
    photo,
    request=None,
    upload_details=None,
    processing_status=None,
    extra_info=None,
):
    """
    Log photo upload with detailed information.

    Args:
        user: User uploading the photo
        photo: Photo object that was uploaded
        request: Django request object
        upload_details: Dict with upload information (batch_size, total_photos, etc.)
        processing_status: Dict with processing status from photo.get_processing_status()
        extra_info: Additional information dict
    """
    extra_info = extra_info or {}
    if upload_details:
        extra_info["upload_details"] = upload_details
    if processing_status:
        extra_info["processing_status"] = processing_status

    log_photo_action_json(
        user=user,
        action="photo_upload",
        photo=photo,
        request=request,
        extra_info=extra_info,
    )


def log_photo_delete_json(
    user,
    photo,
    request=None,
    extra_info=None,
):
    """
    Log photo deletion.

    Args:
        user: User deleting the photo
        photo: Photo object that was deleted
        request: Django request object
        extra_info: Additional information dict
    """
    log_photo_action_json(
        user=user,
        action="photo_delete",
        photo=photo,
        request=request,
        extra_info=extra_info,
    )


def log_photo_edit_json(
    user,
    photo,
    request=None,
    changes=None,
    extra_info=None,
):
    """
    Log photo editing.

    Args:
        user: User editing the photo
        photo: Photo object that was edited
        request: Django request object
        changes: Dict describing what was changed
        extra_info: Additional information dict
    """
    extra_info = extra_info or {}
    if changes:
        extra_info["changes"] = changes

    log_photo_action_json(
        user=user,
        action="photo_edit",
        photo=photo,
        request=request,
        extra_info=extra_info,
    )


def log_photo_view_json(
    user,
    photo,
    request=None,
    view_type="detail",  # detail, gallery, public_gallery
    extra_info=None,
):
    """
    Log photo viewing.

    Args:
        user: User viewing the photo
        photo: Photo object being viewed
        request: Django request object
        view_type: Type of view (detail, gallery, public_gallery)
        extra_info: Additional information dict
    """
    extra_info = extra_info or {}
    extra_info["view_type"] = view_type

    log_photo_action_json(
        user=user,
        action="photo_view",
        photo=photo,
        request=request,
        extra_info=extra_info,
    )


def log_photo_bulk_action_json(
    user,
    action,
    photo_ids,
    request=None,
    results=None,
    extra_info=None,
):
    """
    Log bulk photo actions.

    Args:
        user: User performing the bulk action
        action: Type of bulk action (bulk_delete, bulk_public, etc.)
        photo_ids: List of photo IDs affected
        request: Django request object
        results: Dict with results of the bulk action
        extra_info: Additional information dict
    """
    extra_info = extra_info or {}
    extra_info["photo_ids"] = photo_ids
    extra_info["photo_count"] = len(photo_ids)
    if results:
        extra_info["results"] = results

    log_photo_action_json(
        user=user,
        action=f"bulk_{action}",
        photo=None,  # No single photo for bulk actions
        request=request,
        extra_info=extra_info,
    )
