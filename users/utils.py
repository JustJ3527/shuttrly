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
from datetime import datetime, timedelta, date  # Date and time management
import base64  # Encoding images to base64

# === Third-Party Imports ===
import requests  # HTTP requests for IP location
import pyotp  # TOTP generation and verification
import qrcode  # QR code generation
from user_agents import parse  # Parse user agent strings
import hashlib

# === Decorators ===
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# === Django Imports ===
from django.conf import settings  # Django settings access
from django.core.mail import send_mail  # Email sending
from django.core.files.storage import default_storage  # File storage API
from django.utils import timezone  # Timezone-aware datetime
from django.utils.http import http_date  # HTTP date formatting
from django.contrib.auth import get_backends, get_user_model
from django.shortcuts import redirect
from django.contrib.auth import login
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate

# === Local Imports ===
from .models import (
    TrustedDevice,
    CustomUser,
    PendingFileDeletion,
)  # Model for trusted devices
from logs.utils import log_user_action_json


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
def generate_email_code():
    """Generate a numeric verification code of specified length."""
    return "".join(random.choices(string.digits, k=6))


def send_email_code(email, code, subject=None, message=None):
    """
    Envoie un code par email avec possibilité de personnaliser le sujet et le message.
    """
    if subject is None:
        subject = "Code de vérification"
    if message is None:
        message = f"Votre code est : {code}"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_2FA_email(user, code):
    print(
        f"Sending 2FA code to {user.email}"
    )  # For demo purposes, replace with actual email sending logic
    """
    Fonction pour envoyer l'email de vérification
    À adapter selon votre configuration email
    """
    subject = "2FA Code de vérification"
    message = f"Your 2FA code is : {code}\n\nCe code expire dans 10 minutes."

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False


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


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def is_trusted_device(request, user):
    """
    Check if the current request is from a trusted device.

    Args:
        request: HTTP request object
        user: User object

    Returns:
        bool: True if the device is trusted, False otherwise
    """
    for cookie_name, token in request.COOKIES.items():
        if cookie_name.startswith(f"trusted_device_{user.pk}"):
            token_hash = hash_token(token)
            device = TrustedDevice.objects.filter(
                user=user,
                device_token=token_hash,
                expires_at__gt=timezone.now(),
            ).first()
            if device:
                # Update device usage
                device.last_used_at = timezone.now()
                device.ip_address = get_client_ip(request)
                device.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
                device.save(update_fields=["last_used_at", "ip_address", "user_agent"])
                return True
    return False


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


# def generate_verification_code():
#     """Génère un code de vérification à 6 chiffres"""
#     return "".join(random.choices(string.digits, k=6))


def calculate_age(birth_date):
    """Calcule l'âge à partir de la date de naissance"""
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def can_resend_code(session_data):
    """Vérifie si on peut renvoyer un code"""
    code_sent_at = session_data.get("code_sent_at")
    if not code_sent_at:
        return True

    try:
        sent_time = datetime.fromisoformat(
            code_sent_at.replace("Z", "+00:00")
            if code_sent_at.endswith("Z")
            else code_sent_at
        )
        if timezone.is_naive(sent_time):
            sent_time = timezone.make_aware(sent_time)

        # Attendre 2 minutes avant de permettre un renvoi
        return (timezone.now() - sent_time).total_seconds() > 20
    except:
        return True


def send_verification_email(email, code):
    print(
        f"Sending verification email to {email}"
    )  # For demo purposes, replace with actual email sending logic
    """
    Fonction pour envoyer l'email de vérification
    À adapter selon votre configuration email
    """

    try:
        subject = "Code de vérification"
        message = f"Votre code de vérification est : {code}\n\nCe code expire dans 10 minutes."

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False


def get_device_name(request):
    """Génère un nom d'appareil basé sur le user agent"""
    user_agent = get_user_agent(request)

    # Try to use analyze_user_agent first
    try:
        ua_info = analyze_user_agent(user_agent)
        device_type = ua_info.get("device_type", "Unknown Device")
        if device_type != "Unknown device":
            return device_type
    except:
        pass

    # Fallback to simple string matching
    user_agent_lower = user_agent.lower()

    if "iphone" in user_agent_lower:
        return "iPhone"
    elif "ipad" in user_agent_lower:
        return "iPad"
    elif "android" in user_agent_lower:
        return "Android Device"
    elif "windows" in user_agent_lower:
        return "Windows PC"
    elif "macintosh" in user_agent_lower or "mac os" in user_agent_lower:
        return "Mac"
    elif "linux" in user_agent_lower:
        return "Linux PC"
    elif "chrome" in user_agent_lower:
        return "Chrome Browser"
    elif "firefox" in user_agent_lower:
        return "Firefox Browser"
    elif "safari" in user_agent_lower:
        return "Safari Browser"
    else:
        return "Unknown Device"


def is_safe_url(url, allowed_hosts, require_https=False):
    """Vérifie si une URL de redirection est sûre"""
    from urllib.parse import urlparse

    if not url:
        return False

    parsed = urlparse(url)

    # URL relative
    if not parsed.netloc:
        return True

    # Vérifier le host
    if parsed.netloc not in allowed_hosts:
        return False

    # Vérifier HTTPS si requis
    if require_https and parsed.scheme != "https":
        return False

    return True


from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages


def login_success(
    request, user, ip, user_agent, location, twofa_method=None, remember_device=False
):
    print("login_success called")
    user.backend = (
        f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
    )
    login(request, user)

    user.is_online = True
    user.last_login_date = timezone.now()
    user.last_login_ip = ip
    user.save()

    next_url = request.GET.get("next") or request.POST.get("next")
    redirect_url = (
        next_url
        if is_safe_url(next_url, allowed_hosts={request.get_host()})
        else reverse("profile")
    )
    response = HttpResponseRedirect(redirect_url)

    print(f"remember_device: {remember_device}")

    if remember_device:
        trusted_tokens = [
            value
            for key, value in request.COOKIES.items()
            if key.startswith(f"trusted_device_{user.pk}")
        ]

        device = None
        for token in trusted_tokens:
            hashed_token = hash_token(token)
            device = TrustedDevice.objects.filter(
                user=user, device_token=hashed_token
            ).first()
            if device:
                break

        if device:
            device.last_used_at = timezone.now()
            device.ip_address = ip
            device.user_agent = user_agent[:255]
            if location:
                device.location = location
            device.save(
                update_fields=["last_used_at", "ip_address", "user_agent", "location"]
            )
        else:
            cookie_name = f"trusted_device_{user.pk}"
            max_age_days = 30
            max_age = max_age_days * 24 * 60 * 60
            expires = http_date(timezone.now().timestamp() + max_age)
            token = f"{user.pk}-{uuid.uuid4().hex}"
            token_hash = hash_token(token)

            # Analyze user agent for better device information
            device_info = {}
            try:
                ua_info = analyze_user_agent(user_agent)
                device_info = {
                    "device_type": ua_info.get("device_type", "Unknown Device"),
                    "device_family": ua_info.get("device_family", "Unknown"),
                    "browser_family": ua_info.get("browser_family", "Unknown"),
                    "browser_version": ua_info.get("browser_version", ""),
                    "os_family": ua_info.get("os_family", "Unknown"),
                    "os_version": ua_info.get("os_version", ""),
                }
            except Exception as e:
                # Fallback to simple device name
                try:

                    class MockRequest:
                        def __init__(self, user_agent):
                            self.META = {"HTTP_USER_AGENT": user_agent}

                    mock_request = MockRequest(user_agent)
                    device_info = {
                        "device_type": get_device_name(mock_request),
                        "device_family": "Unknown",
                        "browser_family": "Unknown",
                        "browser_version": "",
                        "os_family": "Unknown",
                        "os_version": "",
                    }
                except:
                    device_info = {
                        "device_type": "Unknown Device",
                        "device_family": "Unknown",
                        "browser_family": "Unknown",
                        "browser_version": "",
                        "os_family": "Unknown",
                        "os_version": "",
                    }

            TrustedDevice.objects.create(
                user=user,
                device_token=token_hash,
                user_agent=user_agent[:255],
                ip_address=ip,
                location=location or "",
                expires_at=timezone.now() + timedelta(days=max_age_days),
                device_type=device_info.get("device_type", "Unknown Device"),
                device_family=device_info.get("device_family", "Unknown"),
                browser_family=device_info.get("browser_family", "Unknown"),
                browser_version=device_info.get("browser_version", ""),
                os_family=device_info.get("os_family", "Unknown"),
                os_version=device_info.get("os_version", ""),
            )

            response.set_cookie(
                cookie_name,
                token,
                max_age=max_age,
                expires=expires,
                secure=True,
                httponly=True,
                samesite="Lax",
            )

        request.session.pop("remember_device", None)  # Une seule fois ici

    log_user_action_json(
        user=user,
        action="login",
        request=request,
        ip_address=ip,
        extra_info={
            "twofa_method": twofa_method,
            "remember_device": remember_device,
            "user_agent": user_agent[:200],
            "location": location,
        },
    )

    welcome_msg = f"Bienvenue {user.first_name} !"
    if twofa_method == "trusted_device":
        welcome_msg += " (Appareil de confiance)"
    elif twofa_method:
        welcome_msg += " Connexion sécurisée"
    messages.success(request, welcome_msg)

    # Clean up session data at the end
    request.session.pop("login_data", None)
    request.session.pop("pre_2fa_user_id", None)
    # Note: remember_device is already cleaned up earlier in the function

    return response


def get_user_from_session(request):
    """Récupère l'utilisateur depuis la session"""
    user_id = request.session.get("pre_2fa_user_id")
    if user_id:
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            pass
    return None


def initialize_2fa_session_data(request, user, code):
    """
    Initialize session data for 2FA process, similar to registration
    """
    session_data = request.session.get("login_data", {})
    session_data.update(
        {
            "email": user.email,
            "verification_code": code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        }
    )
    request.session["login_data"] = session_data
    return session_data


def initialize_login_session_data(request, user, code=None):
    """
    Initialize session data for login process
    Similar to register but for login flow
    """
    session_data = request.session.get("login_data", {})
    session_data.update(
        {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_2fa_enabled": user.email_2fa_enabled,
            "totp_enabled": user.totp_enabled,
            "code_attempts": 0,
        }
    )

    if code:
        session_data.update(
            {
                "verification_code": code,
                "code_sent_at": timezone.now().isoformat(),
            }
        )

    request.session["login_data"] = session_data
    return session_data


def handle_login_step_1_credentials(request):
    """
    Handle step 1 of login: email/username and password validation
    Returns (success, user, error_message)
    """
    from .forms import LoginForm

    form = LoginForm(request.POST)
    if not form.is_valid():
        return False, None, "Invalid form data"

    identifier = form.cleaned_data["email"]
    password = form.cleaned_data["password"]
    remember_device = form.cleaned_data.get("remember_device", False)

    # Store remember_device in session
    request.session["remember_device"] = remember_device

    # Find user by email or username
    user_qs = CustomUser.objects.filter(Q(email=identifier) | Q(username=identifier))

    if not user_qs.exists():
        return False, None, "No account found with this email/username"

    user = user_qs.first()

    # Authenticate user
    authenticated_user = authenticate(request, username=identifier, password=password)
    if authenticated_user is None:
        return False, None, "Incorrect email/username or password"

    # Check if email is verified
    if not user.is_email_verified:
        return False, None, "Please verify your email before logging in"

    return True, user, None


def handle_login_step_2_2fa_choice(request):
    """
    Handle step 2 of login: 2FA method choice
    Returns (success, user, error_message)
    """
    from .forms import Choose2FAMethodForm

    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")

    if not user_id:
        return False, None, "Session expired. Please try again."

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return False, None, "User not found"

    form = Choose2FAMethodForm(request.POST)
    if not form.is_valid():
        return False, user, "Invalid 2FA method selection"

    method = form.cleaned_data["twofa_method"]

    if method == "email" and not user.email_2fa_enabled:
        return False, user, "Email 2FA is not enabled for this account"

    if method == "totp" and not user.totp_enabled:
        return False, user, "TOTP 2FA is not enabled for this account"

    # Store the chosen method
    session_data["chosen_2fa_method"] = method
    request.session["login_data"] = session_data

    return True, user, None


def handle_login_step_3_2fa_verification_logic(request):
    """
    Handle step 3 of login: 2FA code verification
    Returns (success, user, error_message)
    """
    from .forms import Email2FAForm, TOTP2FAForm

    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    chosen_method = session_data.get("chosen_2fa_method")

    if not user_id or not chosen_method:
        return False, None, "Session expired. Please try again."

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return False, None, "User not found"

    # Validate the submitted code
    if chosen_method == "email":
        form = Email2FAForm(request.POST)
        if not form.is_valid():
            return False, user, "Invalid verification code format"

        submitted_code = form.cleaned_data["twofa_code"]
        stored_code = session_data.get("verification_code")
        code_sent_at = session_data.get("code_sent_at")
        attempts = session_data.get("code_attempts", 0)

        # Check attempts
        if attempts >= 3:
            return False, user, "Too many attempts. Request a new code."

        # Check expiration (10 minutes)
        if code_sent_at:
            sent_time = datetime.fromisoformat(
                code_sent_at.replace("Z", "+00:00")
                if code_sent_at.endswith("Z")
                else code_sent_at
            )
            if timezone.is_naive(sent_time):
                sent_time = timezone.make_aware(sent_time)

            if (timezone.now() - sent_time).total_seconds() > 600:  # 10 minutes
                return False, user, "Code has expired. Request a new code."

            if submitted_code == stored_code:
                # Clear session data after successful verification
                request.session.pop("login_data", None)
                return True, user, None
            else:
                attempts += 1
                session_data["code_attempts"] = attempts
                request.session["login_data"] = session_data
                return (
                    False,
                    user,
                    f"Incorrect code. {3-attempts} remaining attempt(s).",
                )

        return False, user, "Session error. Please try again."

    elif chosen_method == "totp":
        form = TOTP2FAForm(request.POST)
        if not form.is_valid():
            return False, user, "Invalid TOTP code format"

        submitted_code = form.cleaned_data["twofa_code"]

        if verify_totp(user.twofa_totp_secret, submitted_code):
            # Clear session data after successful verification
            request.session.pop("login_data", None)
            return True, user, None
        else:
            return False, user, "Invalid TOTP code"

    return False, user, "Invalid 2FA method"


def handle_login_resend_code(request, user):
    """
    Handle resend code request for login 2FA
    Returns (success, message)
    """
    session_data = request.session.get("login_data", {})
    return handle_resend_code_request(request, session_data, user, "email")


def get_login_step_progress(step):
    """
    Calculate progress percentage for login steps
    """
    step_progress = {
        "login": 33,
        "choose_2fa": 66,
        "email_2fa": 100,
        "totp_2fa": 100,
    }
    return step_progress.get(step, 0)


def cleanup_login_session(request):
    """
    Clean up login session data
    """
    request.session.pop("login_data", None)
    request.session.pop("remember_device", None)
    request.session.pop("pre_2fa_user_id", None)


def handle_resend_code_request(request, session_data, user, email_field="email"):
    """
    Common function to handle resend code requests for both register and login
    Returns (success, message)
    """
    if not can_resend_code(session_data):
        return False, "Please wait before requesting a new code"

    # Generate and send new code
    new_code = generate_email_code()

    # Update session data
    session_data.update(
        {
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        }
    )

    # Determine which session key to use
    if "user_id" in session_data:
        request.session["login_data"] = session_data
        # Also update user object for login
        user.email_2fa_code = new_code
        user.email_2fa_sent_at = timezone.now()
        user.save()
    else:
        request.session["register_data"] = session_data

    # Send email
    email = session_data.get(email_field)
    if email:
        success = send_verification_email(email, new_code)
        if success:
            return True, "A new verification code has been sent to your email address."
        else:
            return False, "Error sending verification code. Please try again."
    else:
        return False, "Email not found in session"


def add_form_error_with_message(form, field, message):
    """
    Add error to form and also add a message for display
    """
    form.add_error(field, message)
    return form
