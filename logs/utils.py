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

    # Construction de l’entrée de log
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
