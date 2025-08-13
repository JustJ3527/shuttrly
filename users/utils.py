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
import base64
import hashlib
import io
import os
import random
import string
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, urlencode

# === Third-Party Imports ===
import pyotp
import qrcode
import requests
from user_agents import parse

# === Django Imports ===
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_backends, get_user_model, login
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.http import http_date

# === Local Imports ===
from logs.utils import log_user_action_json
from .models import CustomUser, PendingFileDeletion, TrustedDevice
from .forms import LoginForm, Email2FAForm, TOTP2FAForm, Choose2FAMethodForm

# === Constants ===
from .constants import (
    EMAIL_CODE_RESEND_DELAY_SECONDS,
    EMAIL_CODE_EXPIRY_SECONDS,
    MAX_2FA_ATTEMPTS,
)

# === Logger Setup ===
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# IP UTILITIES
# =============================================================================


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


# =============================================================================
# PROFILE PICTURE DELETION SCHEDULING AND CLEANUP
# =============================================================================


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
            logger.warning(f'File {file_path} still in use by: {", ".join(usernames)}')
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking if file is in use {file_path}: {str(e)}")
        # Return True as a safety fallback
        return True


# =============================================================================
# USER DATA UTILITIES
# =============================================================================


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


# =============================================================================
# 2FA EMAIL CODE UTILITIES
# =============================================================================


def generate_email_code():
    """Generate a numeric verification code of specified length."""
    return "".join(random.choices(string.digits, k=6))


def send_2FA_email(user, code):
    """
    Send a 2FA code to the user's email.
    """
    subject = "Verification Code - Shuttrly"

    html_content = render_to_string(
        "emails/2fa_code.html",
        {
            "user": user,
            "code": code,
            "expiration_minutes": 10,
        },
    )

    # Text version (fallback if HTML is disabled)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True

    except Exception as e:
        print(f"Error sending 2FA email: {e}")
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


# =============================================================================
# TOTP (TIME-BASED ONE-TIME PASSWORD) UTILITIES
# =============================================================================


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


# =============================================================================
# TRUSTED DEVICE MANAGEMENT
# =============================================================================


def hash_token(token: str) -> str:
    """Hash a token using SHA256."""
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


# =============================================================================
# IP GEOLOCATION
# =============================================================================


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


# =============================================================================
# USER AGENT ANALYSIS
# =============================================================================


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


def calculate_age(birth_date):
    """Calculate age from birth date."""
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def can_resend_code(session_data):
    """Check if a code can be resent."""
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

        # Wait 2 minutes before allowing resend
        return (
            timezone.now() - sent_time
        ).total_seconds() > EMAIL_CODE_RESEND_DELAY_SECONDS
    except:
        return True


def send_verification_email(email, code):
    """
    Function to send verification email.
    To be adapted according to your email configuration.
    """
    print(f"Sending verification email to {email}")  # For demo purposes

    try:
        subject = "Verification Code"
        message = (
            f"Your verification code is: {code}\n\nThis code expires in 10 minutes."
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False


def get_device_name(request):
    """Generate a device name based on user agent."""
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
    """Check if a redirect URL is safe."""
    if not url:
        return False

    parsed = urlparse(url)

    # Relative URL
    if not parsed.netloc:
        return True

    # Check host
    if parsed.netloc not in allowed_hosts:
        return False

    # Check HTTPS if required
    if require_https and parsed.scheme != "https":
        return False

    return True


# =============================================================================
# LOGIN AND AUTHENTICATION UTILITIES
# =============================================================================


def login_success(
    request, user, ip, user_agent, location, twofa_method=None, remember_device=False
):
    """
    Handle successful login and setup trusted device if requested.
    This function manages the complete login flow including device trust.

    Args:
        request: HTTP request object
        user: Authenticated user object
        ip: Client IP address
        user_agent: User agent string from browser
        location: Geographic location info (optional)
        twofa_method: Method used for 2FA verification
        remember_device: Whether to remember this device for future logins

    Returns:
        HttpResponseRedirect: Redirect response after successful login
    """
    print("login_success called")

    # Set the authentication backend for the user
    # This is required for Django's authentication system to work properly
    user.backend = (
        f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
    )
    login(request, user)

    # Update user status and login information
    user.is_online = True
    user.last_login_date = timezone.now()
    user.last_login_ip = ip
    user.save()

    # Handle redirect to next page or default to profile
    # next_url can come from GET or POST parameters
    next_url = request.GET.get("next") or request.POST.get("next")
    redirect_url = (
        next_url
        if is_safe_url(next_url, allowed_hosts={request.get_host()})
        else reverse("profile")
    )
    response = HttpResponseRedirect(redirect_url)

    print(f"remember_device: {remember_device}")

    if remember_device:
        # Check for existing trusted device cookies
        # Look for cookies that start with 'trusted_device_{user_id}'
        trusted_tokens = [
            value
            for key, value in request.COOKIES.items()
            if key.startswith(f"trusted_device_{user.pk}")
        ]

        # Try to find an existing trusted device
        device = None
        for token in trusted_tokens:
            hashed_token = hash_token(token)
            device = TrustedDevice.objects.filter(
                user=user, device_token=hashed_token
            ).first()
            if device:
                break

        if device:
            # Update existing device with current usage information
            device.last_used_at = timezone.now()
            device.ip_address = ip
            device.user_agent = user_agent[:255]  # Limit to database field size
            if location:
                device.location = location
            device.save(
                update_fields=["last_used_at", "ip_address", "user_agent", "location"]
            )
        else:
            # Create new trusted device with 30-day expiration
            cookie_name = f"trusted_device_{user.pk}"
            max_age_days = 30
            max_age = max_age_days * 24 * 60 * 60  # Convert to seconds
            expires = http_date(timezone.now().timestamp() + max_age)

            # Generate unique token: user_id + random UUID
            token = f"{user.pk}-{uuid.uuid4().hex}"
            token_hash = hash_token(token)

            # Analyze user agent for better device information
            # This provides detailed browser/OS/device information
            device_info = _get_device_info_from_user_agent(user_agent)

            # Create the trusted device record in database
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

            # Set secure HTTP-only cookie for trusted device
            # This cookie will be used to identify the device on future visits
            response.set_cookie(
                cookie_name,
                token,
                max_age=max_age,
                expires=expires,
                secure=True,  # Only sent over HTTPS
                httponly=True,  # Not accessible via JavaScript
                samesite="Lax",  # CSRF protection
            )

        # Clean up session flag - only needed once during login
        request.session.pop("remember_device", None)

    # Log the successful login action for security monitoring
    log_user_action_json(
        user=user,
        action="login",
        request=request,
        ip_address=ip,
        extra_info={
            "twofa_method": twofa_method,
            "remember_device": remember_device,
            "user_agent": user_agent[:200],  # Limit log entry size
            "location": location,
        },
    )

    # Display personalized welcome message
    welcome_msg = f"Welcome {user.first_name}!"
    if twofa_method == "trusted_device":
        welcome_msg += " (Trusted Device)"
    elif twofa_method:
        welcome_msg += " Secure Login"
    messages.success(request, welcome_msg)

    # Clean up session data to prevent memory leaks
    request.session.pop("login_data", None)
    request.session.pop("pre_2fa_user_id", None)
    request.session.pop("current_login_step", None)  # Clean up current step

    return response


def _get_device_info_from_user_agent(user_agent):
    """
    Extract device information from user agent string.
    Returns a dictionary with device details.

    This function attempts to parse the user agent string to extract:
    - Device type (Desktop, Mobile, Tablet, Bot)
    - Browser information (Chrome, Firefox, Safari, etc.)
    - Operating system details (Windows, macOS, Linux, etc.)

    Args:
        user_agent: Raw user agent string from browser

    Returns:
        dict: Device information with fallback values if parsing fails
    """
    try:
        # Try to use the user_agents library for detailed parsing
        ua_info = analyze_user_agent(user_agent)
        return {
            "device_type": ua_info.get("device_type", "Unknown Device"),
            "device_family": ua_info.get("device_family", "Unknown"),
            "browser_family": ua_info.get("browser_family", "Unknown"),
            "browser_version": ua_info.get("browser_version", ""),
            "os_family": ua_info.get("os_family", "Unknown"),
            "os_version": ua_info.get("os_version", ""),
        }
    except Exception as e:
        # Fallback to simple device name detection if parsing fails
        try:
            # Create a mock request object to use with get_device_name function
            # This allows us to reuse existing device detection logic
            class MockRequest:
                def __init__(self, user_agent):
                    self.META = {"HTTP_USER_AGENT": user_agent}

            mock_request = MockRequest(user_agent)
            return {
                "device_type": get_device_name(mock_request),
                "device_family": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "",
                "os_family": "Unknown",
                "os_version": "",
            }
        except:
            # Final fallback with default values if everything fails
            return {
                "device_type": "Unknown Device",
                "device_family": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "",
                "os_family": "Unknown",
                "os_version": "",
            }


def get_user_from_session(request):
    """
    Retrieve user from session data.

    This function is used during the 2FA process to get the user
    who has already been authenticated but needs to complete 2FA.

    Args:
        request: HTTP request object

    Returns:
        CustomUser or None: User object if found, None otherwise
    """
    user_id = request.session.get("pre_2fa_user_id")
    if user_id:
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            pass
    return None


def initialize_2fa_session_data(request, user, code):
    """
    Initialize session data for 2FA process, similar to registration.

    This function sets up the session with verification code and metadata
    needed for the 2FA verification step.

    Args:
        request: HTTP request object
        user: User object
        code: Verification code to store in session

    Returns:
        dict: Updated session data
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
    Initialize session data for login process.
    Similar to register but for login flow.

    This function stores user information and 2FA settings in the session
    to be used throughout the multi-step login process.

    Args:
        request: HTTP request object
        user: User object
        code: Optional verification code (for email 2FA)

    Returns:
        dict: Updated session data
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


# =============================================================================
# LOGIN STEP HANDLERS
# =============================================================================


def handle_login_step_1_credentials(request):
    """
    Handle step 1 of login: email/username and password validation.

    This is the first step of the multi-step login process.
    It validates user credentials and checks if email verification is complete.

    Args:
        request: HTTP request object with POST data

    Returns:
        tuple: (success: bool, user: CustomUser or None, error_message: str or None)
    """

    form = LoginForm(request.POST)
    if not form.is_valid():
        return False, None, "Invalid form data"

    identifier = form.cleaned_data["email"]
    password = form.cleaned_data["password"]
    remember_device = form.cleaned_data.get("remember_device", False)

    # Store remember_device preference in session for later use
    request.session["remember_device"] = remember_device

    # Determine if input is email or username (more robust detection)
    # Check for @ symbol and basic email structure
    is_email = (
        "@" in identifier
        and "." in identifier.split("@")[-1]
        and len(identifier.split("@")[-1]) > 1
    )

    # Find user by email or username (flexible login)
    user_qs = CustomUser.objects.filter(Q(email=identifier) | Q(username=identifier))

    if not user_qs.exists():
        if is_email:
            # Format email for better display (only after submission)
            formatted_email = identifier.lower().strip()
            return (
                False,
                None,
                f"No account found with the email address: {formatted_email}",
            )
        else:
            # Format username for better display
            formatted_username = identifier.lower().strip()
            return (
                False,
                None,
                f"No account found with the username: {formatted_username}",
            )

    user = user_qs.first()

    # Authenticate user with Django's built-in authentication
    authenticated_user = authenticate(request, username=identifier, password=password)
    if authenticated_user is None:
        if is_email:
            formatted_email = identifier.lower().strip()
            return (
                False,
                None,
                f"Incorrect password for the email address: {formatted_email}",
            )
        else:
            formatted_username = identifier.lower().strip()
            return (
                False,
                None,
                f"Incorrect password for the username: {formatted_username}",
            )

    # Check if email is verified (security requirement)
    if not user.is_email_verified:
        return False, None, "Please verify your email before logging in"

    return True, user, None


def handle_login_step_2_2fa_choice(request):
    """
    Handle step 2 of login: 2FA method choice.

    After successful credential validation, user chooses their 2FA method.
    This step validates that the chosen method is enabled for the user.

    Args:
        request: HTTP request object with POST data

    Returns:
        tuple: (success: bool, user: CustomUser or None, error_message: str or None)
    """

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

    # Validate that the chosen 2FA method is enabled for this user
    if method == "email" and not user.email_2fa_enabled:
        return False, user, "Email 2FA is not enabled for this account"

    if method == "totp" and not user.totp_enabled:
        return False, user, "TOTP 2FA is not enabled for this account"

    # Store the chosen method in session for the next step
    session_data["chosen_2fa_method"] = method
    request.session["login_data"] = session_data

    return True, user, None


def handle_login_step_3_2fa_verification_logic(request):
    """
    Handle step 3 of login: 2FA code verification.

    This is the final step where the user provides their 2FA code.
    The function routes to the appropriate verification handler based on the method.

    Args:
        request: HTTP request object with POST data

    Returns:
        tuple: (success: bool, user: CustomUser or None, error_message: str or None)
    """

    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    chosen_method = session_data.get("chosen_2fa_method")

    if not user_id or not chosen_method:
        return False, None, "Session expired. Please try again."

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return False, None, "User not found"

    # Route to appropriate verification handler based on chosen method
    if chosen_method == "email":
        return _handle_email_2fa_verification(request, session_data, user)
    elif chosen_method == "totp":
        return _handle_totp_2fa_verification(request, user)

    return False, user, "Invalid 2FA method"


def _handle_email_2fa_verification(request, session_data, user):
    """
    Handle email 2FA verification logic.

    This function validates the email verification code with the following checks:
    - Code format validation
    - Attempt limit (max 3 attempts)
    - Code expiration (10 minutes)
    - Code matching

    Args:
        request: HTTP request object
        session_data: Current session data
        user: User object

    Returns:
        tuple: (success: bool, user: CustomUser or None, error_message: str or None)
    """

    form = Email2FAForm(request.POST)
    if not form.is_valid():
        return False, user, "Invalid verification code format"

    submitted_code = form.cleaned_data["twofa_code"]
    stored_code = session_data.get("verification_code")
    code_sent_at = session_data.get("code_sent_at")
    attempts = session_data.get("code_attempts", 0)

    # Check attempt limit to prevent brute force attacks
    if attempts >= 3:
        return False, user, "Too many attempts. Request a new code."

    # Check code expiration (10 minutes from when code was sent)
    if code_sent_at:
        # Parse ISO format timestamp and handle timezone
        sent_time = datetime.fromisoformat(
            code_sent_at.replace("Z", "+00:00")
            if code_sent_at.endswith("Z")
            else code_sent_at
        )
        if timezone.is_naive(sent_time):
            sent_time = timezone.make_aware(sent_time)

        # Check if code has expired
        if (timezone.now() - sent_time).total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:
            return False, user, "Code has expired. Request a new code."

        # Validate the submitted code against stored code
        if submitted_code == stored_code:
            # Clear session data after successful verification
            request.session.pop("login_data", None)
            return True, user, None
        else:
            # Increment attempt counter and update session
            attempts += 1
            session_data["code_attempts"] = attempts
            request.session["login_data"] = session_data
            return (
                False,
                user,
                f"Incorrect code. {3-attempts} remaining attempt(s).",
            )

    return False, user, "Session error. Please try again."


def _handle_totp_2fa_verification(request, user):
    """
    Handle TOTP 2FA verification logic.

    This function validates the TOTP code using the user's secret key.
    TOTP codes are time-based and automatically expire.

    Args:
        request: HTTP request object
        user: User object with TOTP secret

    Returns:
        tuple: (success: bool, user: CustomUser or None, error_message: str or None)
    """

    form = TOTP2FAForm(request.POST)
    if not form.is_valid():
        return False, user, "Invalid TOTP code format"

    submitted_code = form.cleaned_data["twofa_code"]

    # Check if user has TOTP enabled and has a valid secret
    if not user.totp_enabled or not user.twofa_totp_secret:
        return False, user, "TOTP 2FA is not enabled for this account"

    # Verify TOTP code using user's secret key
    if verify_totp(user.twofa_totp_secret, submitted_code):
        # Clear session data after successful verification
        request.session.pop("login_data", None)
        return True, user, None
    else:
        return False, user, "Invalid TOTP code"


def handle_login_resend_code(request, user):
    """
    Handle resend code request for login 2FA.

    This function allows users to request a new verification code
    if the previous one expired or was lost.

    Args:
        request: HTTP request object
        user: User object

    Returns:
        tuple: (success: bool, message: str)
    """
    session_data = request.session.get("login_data", {})
    return handle_resend_code_request(request, session_data, user, "email")


# =============================================================================
# SESSION MANAGEMENT AND UTILITIES
# =============================================================================


def get_login_step_progress(step):
    """
    Calculate progress percentage for login steps.

    This function provides visual feedback to users about their progress
    through the multi-step login process.

    Args:
        step: Current login step identifier

    Returns:
        int: Progress percentage (0-100)
    """
    step_progress = {
        "login": 33,  # Step 1: Credentials
        "choose_2fa": 66,  # Step 2: 2FA Method Selection
        "email_2fa": 100,  # Step 3a: Email 2FA
        "totp_2fa": 100,  # Step 3b: TOTP 2FA
    }
    return step_progress.get(step, 0)


def cleanup_login_session(request):
    """
    Clean up login session data.

    This function removes all temporary session data used during
    the login process to prevent memory leaks and security issues.

    Args:
        request: HTTP request object
    """
    request.session.pop("login_data", None)
    request.session.pop("remember_device", None)
    request.session.pop("pre_2fa_user_id", None)


def handle_resend_code_request(request, session_data, user, email_field="email"):
    """
    Common function to handle resend code requests for both register and login.

    This function generates a new verification code, updates session data,
    and sends the code via email. It handles both registration and login flows.

    Args:
        request: HTTP request object
        session_data: Current session data
        user: User object
        email_field: Key name for email in session data

    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if enough time has passed since last code request using database
    if "user_id" in session_data:
        # Login flow: check user object timing
        if user.email_2fa_sent_at:
            time_since_sent = timezone.now() - user.email_2fa_sent_at
            if time_since_sent.total_seconds() < EMAIL_CODE_RESEND_DELAY_SECONDS:
                return False, "Please wait before requesting a new code"
    else:
        # Registration flow: check session timing (fallback)
        if not can_resend_code(session_data):
            return False, "Please wait before requesting a new code"

    # Generate and send new code
    new_code = generate_email_code()

    # Update session data with new code and reset attempts
    session_data.update(
        {
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        }
    )

    # Determine which session key to use based on context
    if "user_id" in session_data:
        # Login flow: update login_data session
        request.session["login_data"] = session_data
        # Also update user object for immediate use
        user.email_2fa_code = new_code
        user.email_2fa_sent_at = timezone.now()
        user.save()
    else:
        # Registration flow: update register_data session
        request.session["register_data"] = session_data

    # Send email with new verification code
    email = session_data.get(email_field)
    if email:
        if "user_id" in session_data:
            # Login flow: use 2FA email template
            success = send_2FA_email(user, new_code)
        else:
            # Registration flow: use verification email template
            success = send_verification_email(email, new_code)

        if success:
            return True, "A new verification code has been sent to your email address."
        else:
            return False, "Error sending verification code. Please try again."
    else:
        return False, "Email not found in session"


def _calculate_time_until_resend(session_data):
    """
    Calculate time until code can be resent for login flow.

    This function calculates the remaining time before a user can request
    a new 2FA code, based on the user's email_2fa_sent_at timestamp.

    Args:
        session_data: Session data containing user_id

    Returns:
        int: Seconds remaining until resend is allowed (0 if can resend now)
    """
    user_id = session_data.get("user_id")
    if not user_id:
        return 0

    try:
        user = CustomUser.objects.get(id=user_id)
        if user.email_2fa_sent_at:
            time_since_sent = timezone.now() - user.email_2fa_sent_at
            return int(
                max(
                    0, EMAIL_CODE_RESEND_DELAY_SECONDS - time_since_sent.total_seconds()
                )
            )
        return 0
    except CustomUser.DoesNotExist:
        return 0


def add_form_error_with_message(form, field, message):
    """
    Add error to form and also add a message for display.

    This utility function ensures that both form validation errors
    and user-friendly messages are displayed to the user.

    Args:
        form: Django form object
        field: Field name to add error to
        message: Error message to display

    Returns:
        form: Updated form object with error
    """
    form.add_error(field, message)
    return form


# =============================================================================
# 2FA SETTINGS UTILITY FUNCTIONS
# =============================================================================


def get_2fa_resend_status(user):
    """
    Calculate time until resend is available for 2FA codes.

    Args:
        user: CustomUser instance

    Returns:
        dict: Contains 'time_until_resend' and 'can_resend' status
    """
    time_until_resend = 0
    can_resend = True

    if user.email_2fa_sent_at:
        time_since_sent = timezone.now() - user.email_2fa_sent_at
        time_until_resend = max(
            0, EMAIL_CODE_RESEND_DELAY_SECONDS - time_since_sent.total_seconds()
        )
        can_resend = time_until_resend <= 0

    return {"time_until_resend": int(time_until_resend), "can_resend": can_resend}


def get_current_device_token(request, user):
    """
    Get the current device token from cookies.

    Args:
        request: HTTP request object
        user: CustomUser instance

    Returns:
        str: Hashed device token or None
    """
    for cookie_name, token in request.COOKIES.items():
        if cookie_name.startswith(f"trusted_device_{user.pk}"):
            return hash_token(token)
    return None


def enhance_trusted_device_info(device, current_device_token):
    """
    Enhance trusted device with additional information and mark current device.

    Args:
        device: TrustedDevice instance
        current_device_token: Current device token hash

    Returns:
        TrustedDevice: Enhanced device instance
    """
    # Mark current device
    device.is_current_device = device.device_token == current_device_token

    # Calculate if device expires soon (within 7 days)
    if device.expires_at:
        device.expires_soon = (device.expires_at - timezone.now()).days <= 7
    else:
        device.expires_soon = False

    # Use stored device information or analyze if not available
    if not device.device_type and device.user_agent:
        try:
            # Analyze user agent if not already stored
            ua_info = analyze_user_agent(device.user_agent)
            device.device_type = ua_info.get("device_type", "Unknown Device")
            device.device_family = ua_info.get("device_family", "Unknown")
            device.browser_family = ua_info.get("browser_family", "Unknown")
            device.browser_version = ua_info.get("browser_version", "")
            device.os_family = ua_info.get("os_family", "Unknown")
            device.os_version = ua_info.get("os_version", "")

            # Save the analyzed information
            device.save(
                update_fields=[
                    "device_type",
                    "device_family",
                    "browser_family",
                    "browser_version",
                    "os_family",
                    "os_version",
                ]
            )

        except Exception as e:
            # Fallback values
            device.device_type = device.device_type or "Unknown Device"
            device.device_family = device.device_family or "Unknown"
            device.browser_family = device.browser_family or "Unknown"
            device.browser_version = device.browser_version or ""
            device.os_family = device.os_family or "Unknown"
            device.os_version = device.os_version or ""
    else:
        # Use stored values or defaults
        device.device_type = device.device_type or "Unknown Device"
        device.device_family = device.device_family or "Unknown"
        device.browser_family = device.browser_family or "Unknown"
        device.browser_version = device.browser_version or ""
        device.os_family = device.os_family or "Unknown"
        device.os_version = device.os_version or ""

    # Format location if it's a dict
    if isinstance(device.location, dict):
        location_parts = []
        if device.location.get("city"):
            location_parts.append(device.location["city"])
        if device.location.get("region"):
            location_parts.append(device.location["region"])
        if device.location.get("country"):
            location_parts.append(device.location["country"])
        device.location_display = (
            ", ".join(location_parts) if location_parts else "Unknown location"
        )
    else:
        device.location_display = device.location or "Unknown location"

    return device


def handle_2fa_cancel_operation(user, step):
    """
    Handle cancellation of 2FA operations in progress.

    Args:
        user: CustomUser instance
        step: Current step to cancel

    Returns:
        HttpResponseRedirect: Redirect response
    """
    if step == "verify_email_code":
        user.email_2fa_code = ""
        user.email_2fa_sent_at = None
        user.save()
    elif step == "verify_totp":
        user.twofa_totp_secret = ""
        user.save()

    response = HttpResponseRedirect(reverse("personal_settings") + "?step=initial")
    response.delete_cookie("remember_device")
    return response


def handle_enable_email_2fa(user, password):
    """
    Handle enabling email 2FA for a user.

    Args:
        user: CustomUser instance
        password: User's password for verification

    Returns:
        tuple: (success, redirect_url, error_message)
    """
    if not user.check_password(password):
        return False, None, "Incorrect password."

    code = generate_email_code()
    user.email_2fa_code = code
    user.email_2fa_sent_at = timezone.now()
    user.save()
    send_2FA_email(user, code)

    url = reverse("personal_settings") + "?" + urlencode({"step": "verify_email_code"})
    return True, url, None


def handle_verify_email_2fa(user, code):
    """
    Handle verification of email 2FA code.

    Args:
        user: CustomUser instance
        code: Email verification code

    Returns:
        tuple: (success, error_message)
    """
    if is_email_code_valid(user, code):
        user.email_2fa_enabled = True
        user.email_2fa_code = ""
        user.email_2fa_sent_at = None
        user.save()
        return True, None
    else:
        return False, "Invalid or expired code."


def handle_resend_email_2fa_code(user):
    """
    Handle resending of email 2FA code.

    Args:
        user: CustomUser instance

    Returns:
        tuple: (success, redirect_url, error_message)
    """
    delta = (
        (timezone.now() - user.email_2fa_sent_at)
        if user.email_2fa_sent_at
        else timedelta(minutes=999)
    )

    if delta.total_seconds() >= EMAIL_CODE_RESEND_DELAY_SECONDS:
        user.email_2fa_code = generate_email_code()
        user.email_2fa_sent_at = timezone.now()
        user.save()
        send_2FA_email(user, user.email_2fa_code)
        return True, None, "New code sent."
    else:
        return False, None, "Please wait before requesting a new code."


def handle_enable_totp_2fa(user, password):
    """
    Handle enabling TOTP 2FA for a user.

    Args:
        user: CustomUser instance
        password: User's password for verification

    Returns:
        tuple: (success, context_data, error_message)
    """
    if not user.check_password(password):
        return False, None, "Incorrect password."

    secret = generate_totp_secret()
    user.twofa_totp_secret = secret
    user.save()

    uri = get_totp_uri(user, secret)
    qr_base64 = generate_qr_code_base64(uri)

    context_data = {
        "qr_code_url": qr_base64,
        "totp_secret": secret,
        "totp_uri": uri,
        "step": "verify_totp",
    }
    return True, context_data, None


def handle_verify_totp_2fa(user, code):
    """
    Handle verification of TOTP 2FA code.

    Args:
        user: CustomUser instance
        code: TOTP verification code

    Returns:
        tuple: (success, error_message)
    """
    if verify_totp(user.twofa_totp_secret, code):
        # Check if this is for enabling or disabling TOTP
        if not user.totp_enabled:
            # This is for enabling TOTP
            user.totp_enabled = True
            # Don't clear the secret - it's needed for future login verifications
            user.save()
            return True, None
        else:
            # This is for disabling TOTP - clear the secret after verification
            user.twofa_totp_secret = ""
            user.save()
            return True, None
    else:
        return False, "Invalid TOTP code."


def handle_disable_2fa_method(user, password, method):
    """
    Handle disabling of 2FA methods.

    Args:
        user: CustomUser instance
        password: User's password for verification
        method: Method to disable ('email' or 'totp')

    Returns:
        tuple: (success, error_message)
    """
    if not user.check_password(password):
        return False, "Incorrect password."

    if method == "email":
        user.email_2fa_enabled = False
        user.email_2fa_code = ""
        user.email_2fa_sent_at = None
        user.save()
        return True, "Email 2FA disabled successfully!"
    elif method == "totp":
        user.totp_enabled = False
        # Don't clear the secret immediately - it's needed for verification during disable
        # The secret will be cleared after successful verification in handle_verify_totp_2fa
        user.save()
        return True, "TOTP 2FA disabled successfully!"

    return False, "Invalid method specified."


def handle_remove_trusted_device(user, device_id, current_device_token):
    """
    Handle removal of trusted devices.

    Args:
        user: CustomUser instance
        device_id: ID of device to remove
        current_device_token: Current device token hash

    Returns:
        tuple: (success, is_current_device, error_message)
    """
    try:
        device = TrustedDevice.objects.get(id=device_id, user=user)
        is_current_device = device.device_token == current_device_token
        device.delete()
        return True, is_current_device, None
    except TrustedDevice.DoesNotExist:
        return False, False, "Device not found."


def get_2fa_settings_context(user, trusted_devices, step):
    """
    Get context data for 2FA settings view.

    Args:
        user: CustomUser instance
        trusted_devices: List of trusted devices
        step: Current step

    Returns:
        dict: Context data for template
    """
    resend_status = get_2fa_resend_status(user)

    return {
        "trusted_devices": trusted_devices,
        "email_2fa_enabled": user.email_2fa_enabled,
        "totp_enabled": user.totp_enabled,
        "time_until_resend": resend_status["time_until_resend"],
        "can_resend": resend_status["can_resend"],
        "email_code_resend_delay": EMAIL_CODE_RESEND_DELAY_SECONDS,
        "step": step,
    }
