# users/utils.py
"""
Utility functions for user-related operations including:
- IP extraction
- Profile picture deletion scheduling and cleanup
- 2FA email and TOTP handling
- Trusted device management
- User agent analysis
"""

# === Standard Library Imports ===
import os  # File system operations
import io  # For in-memory streams (QR code)
import uuid  # Unique token generation
import random  # For generating codes
import string  # Characters for code generation
from datetime import datetime, timedelta  # Date and time management
import base64  # Encoding images to base64

# === Third-Party Imports ===
import requests  # HTTP requests for IP location
import pyotp  # TOTP generation and verification
import qrcode  # QR code generation
from user_agents import parse  # Parse user agent strings

# === Django Imports ===
from django.conf import settings  # Django settings access
from django.core.mail import send_mail  # Email sending
from django.core.files.storage import default_storage  # File storage API
from django.utils import timezone  # Timezone-aware datetime
from django.utils.http import http_date  # HTTP date formatting
from django.contrib.auth import get_user_model  # Get custom user model

# === Local Imports ===
from .models import TrustedDevice  # Model for trusted devices


# === Logger Setup ===
import logging

logger = logging.getLogger(__name__)


# --- IP Utilities ---
def get_client_ip(request):
    """
    Extract the real client IP address even behind proxies.
    Returns empty string if no IP found.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # First IP in the list is the original client IP
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


# --- Profile Picture Deletion Scheduling and Cleanup ---
def schedule_profile_picture_deletion(file_path, seconds=None):
    """
    Schedule a profile picture file for deletion after a delay.
    Prevents multiple scheduling of the same file.
    """
    try:
        from .models import (
            PendingFileDeletion,
        )  # Local import to avoid circular dependency

        if seconds is None:
            seconds = getattr(settings, "PROFILE_PICTURE_DELETION_DELAY_SECONDS", 86400)

        deletion_date = timezone.now() + timedelta(seconds=seconds)

        existing = PendingFileDeletion.objects.filter(file_path=file_path).first()
        if not existing:
            PendingFileDeletion.objects.create(
                file_path=file_path,
                scheduled_deletion=deletion_date,
                reason="profile_picture_change",
            )
            logger.info(f"Scheduled deletion of {file_path} for {deletion_date}")
        else:
            logger.warning(
                f"File {file_path} already scheduled for deletion on {existing.scheduled_deletion}"
            )

    except Exception as e:
        logger.error(f"Error scheduling deletion for {file_path}: {str(e)}")


def is_file_still_in_use(file_path):
    """
    Check if the given file is still used as a profile picture by any user.
    Returns True if still in use, else False.
    """
    try:
        User = get_user_model()
        users_using_file = User.objects.filter(profile_picture=file_path)
        if users_using_file.exists():
            usernames = list(users_using_file.values_list("username", flat=True))
            logger.warning(f"File {file_path} still in use by: {', '.join(usernames)}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking if file is in use {file_path}: {str(e)}")
        # Return True as a safety fallback
        return True


def cleanup_old_files():
    """
    Delete files whose scheduled deletion time has passed,
    only if they are not still in use.
    Also attempts to delete empty parent directories.
    Returns the count of deleted files.
    """
    try:
        from .models import PendingFileDeletion

        now = timezone.now()
        files_to_delete = PendingFileDeletion.objects.filter(
            scheduled_deletion__lte=now
        )
        total_files = files_to_delete.count()

        logger.info(f"Found {total_files} files to process")

        deleted_count = 0
        skipped_count = 0
        error_count = 0

        for file_deletion in files_to_delete:
            try:
                logger.info(f"Processing file {file_deletion.file_path}")

                if default_storage.exists(file_deletion.file_path):
                    if not is_file_still_in_use(file_deletion.file_path):
                        default_storage.delete(file_deletion.file_path)
                        logger.info(f"Deleted file {file_deletion.file_path}")

                        # Delete parent directory if empty
                        file_full_path = os.path.join(
                            settings.MEDIA_ROOT, file_deletion.file_path
                        )
                        parent_dir = os.path.dirname(file_full_path)
                        try:
                            if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                                os.rmdir(parent_dir)
                                logger.info(f"Deleted empty folder {parent_dir}")
                        except Exception as e:
                            logger.warning(f"Could not delete folder {parent_dir}: {e}")

                        deleted_count += 1
                    else:
                        logger.warning(
                            f"File still in use, skipping {file_deletion.file_path}"
                        )
                        skipped_count += 1
                        continue
                else:
                    logger.info(f"File already deleted {file_deletion.file_path}")

                file_deletion.delete()

            except Exception as e:
                logger.error(f"Error deleting file {file_deletion.file_path}: {str(e)}")
                error_count += 1

        logger.info(
            f"Summary: {deleted_count} deleted, {skipped_count} skipped, {error_count} errors"
        )
        return deleted_count

    except Exception as e:
        logger.error(f"Critical error in cleanup_old_files: {str(e)}")
        return 0


def get_storage_stats():
    """
    Retrieve statistics about files pending deletion:
    total count, existing files, missing files, total size in MB.
    Returns a dict or None if error occurs.
    """
    try:
        from .models import PendingFileDeletion

        pending_files = PendingFileDeletion.objects.all()
        total_size = 0
        existing_files = 0
        missing_files = 0

        for pending in pending_files:
            if default_storage.exists(pending.file_path):
                try:
                    file_size = default_storage.size(pending.file_path)
                    total_size += file_size
                    existing_files += 1
                except Exception:
                    missing_files += 1
            else:
                missing_files += 1

        total_size_mb = total_size / (1024 * 1024)

        return {
            "total_pending": pending_files.count(),
            "existing_files": existing_files,
            "missing_files": missing_files,
            "total_size_mb": round(total_size_mb, 2),
        }

    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        return None


# --- User Data Utilities ---
def get_changes_dict(old_obj, new_obj, changed_fields):
    """
    Create a dictionary showing changes between old and new object for specified fields.
    If field values are files, returns their URLs.
    """
    changes = {}
    for field in changed_fields:
        old_val = getattr(old_obj, field, "")
        new_val = getattr(new_obj, field, "")

        if hasattr(old_val, "url"):
            old_val = old_val.url
        if hasattr(new_val, "url"):
            new_val = new_val.url

        changes[field] = [old_val, new_val]
    return changes


def get_user_agent(request):
    """
    Retrieve the User-Agent string from request headers.
    Returns 'unknown' if missing.
    """
    return request.META.get("HTTP_USER_AGENT", "unknown")


# --- 2FA Email Code Utilities ---
def generate_email_code(length=6):
    """Generate a numeric verification code of specified length."""
    return "".join(random.choices(string.digits, k=length))


def send_email_code(user, code):
    """Send the 2FA verification code to the user's email."""
    subject = "Your 2FA Verification Code"
    message = f"Your verification code is: {code}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def is_email_code_valid(user, input_code):
    """
    Validate input email 2FA code:
    - Checks code existence and expiration (10 minutes)
    - Returns True if valid, else False
    """
    if not user.email_2fa_code or not user.email_2fa_sent_at:
        return False
    expiration = user.email_2fa_sent_at + timedelta(minutes=10)
    return timezone.now() <= expiration and input_code == user.email_2fa_code


# --- TOTP (Time-Based One-Time Password) Utilities ---
def generate_totp_secret():
    """Generate a random base32 secret for TOTP."""
    return pyotp.random_base32()


def get_totp_uri(user, secret):
    """Create a provisioning URI for the authenticator app setup."""
    return pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Shuttrly")


def generate_qr_code_base64(uri):
    """Generate a base64 encoded PNG QR code from a URI."""
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return qr_base64


def verify_totp(secret, code):
    """Verify a TOTP code allowing a 1-step time window for clock skew."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# --- Trusted Device Management ---
def create_trusted_device(
    response, user, request, ip, user_agent, location=None, max_age_days=30
):
    """
    Register or update a trusted device cookie:
    - If device already known, update last usage info
    - Else create new trusted device record and cookie
    """
    token = request.COOKIES.get("trusted_device")

    if token:
        device = TrustedDevice.objects.filter(user=user, device_token=token).first()
        if device:
            device.last_used_at = timezone.now()
            device.ip_address = ip
            device.user_agent = user_agent[:255]  # truncate if too long
            if location:
                device.location = location
            device.save(
                update_fields=["last_used_at", "ip_address", "user_agent", "location"]
            )
            return  # No further action needed

    # New device registration
    token = uuid.uuid4().hex
    TrustedDevice.objects.create(
        user=user,
        device_token=token,
        user_agent=user_agent[:255],
        ip_address=ip,
        location=location or "",
    )

    max_age = max_age_days * 24 * 60 * 60
    expires = http_date(timezone.now().timestamp() + max_age)
    response.set_cookie(
        "trusted_device",
        token,
        max_age=max_age,
        expires=expires,
        secure=True,
        httponly=True,
        samesite="Lax",
    )


def is_trusted_device(request, user):
    """
    Check if the current device (via cookie) is trusted for the user.
    """
    token = request.COOKIES.get("trusted_device")
    if not token:
        return False
    return TrustedDevice.objects.filter(user=user, device_token=token).exists()


# --- IP Geolocation ---
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


# --- User Agent Analysis ---
def analyze_user_agent(ua_string):
    """
    Parse user agent string and return structured info:
    browser, OS, device family, and device type (PC, Mobile, Tablet, Bot).
    """
    user_agent = parse(ua_string)

    browser_family = user_agent.browser.family or "Unknown"
    browser_version = user_agent.browser.version_string or ""

    os_family = user_agent.os.family or "Unknown"
    os_version = user_agent.os.version_string or ""

    device_family = user_agent.device.family or "Unknown"

    if user_agent.is_bot:
        device_type = "Bot / Crawler"
    elif user_agent.is_pc:
        device_type = "Desktop"
    elif user_agent.is_mobile:
        device_type = "Mobile"
    elif user_agent.is_tablet:
        device_type = "Tablet"
    else:
        device_type = "Unknown device"

    return {
        "browser_family": browser_family,
        "browser_version": browser_version,
        "os_family": os_family,
        "os_version": os_version,
        "device_family": device_family,
        "device_type": device_type,
    }
