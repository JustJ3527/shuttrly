"""
Django user management views with detailed JSON logging.

This module contains all user-related views including:
- Registration (6-step process)
- Login (3-step process with 2FA)
- Profile management
- Account deletion
- 2FA settings
- Logout functionality
"""

# === Python Standard Library ===
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
import re

# === Django Imports ===
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_backends, login, logout
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

# === Project Models ===
from .models import CustomUser, TrustedDevice

# === Project Forms ===
from .forms import (
    RegisterStep1Form,
    RegisterStep2Form,
    RegisterStep3Form,
    RegisterStep4Form,
    RegisterStep5Form,
    CustomUserUpdateForm,
    LoginForm,
    Choose2FAMethodForm,
    Email2FAForm,
    TOTP2FAForm,
)

# === Project Utils ===
from .utils import (
    analyze_user_agent,
    calculate_age,
    can_resend_code,
    generate_email_code,
    generate_qr_code_base64,
    generate_totp_secret,
    get_location_from_ip,
    get_totp_uri,
    is_email_code_valid,
    is_trusted_device,
    login_success,
    schedule_profile_picture_deletion,
    send_verification_email,
    verify_totp,
    get_changes_dict,
    get_user_agent,
    get_client_ip,
    hash_token,
    get_user_from_session,
    send_2FA_email,
    initialize_login_session_data,
    get_login_step_progress,
    handle_resend_code_request,
    _calculate_time_until_resend,
    # 2FA Settings utility functions
    get_2fa_resend_status,
    get_current_device_token,
    enhance_trusted_device_info,
    handle_2fa_cancel_operation,
    handle_enable_email_2fa,
    handle_verify_email_2fa,
    handle_resend_email_2fa_code,
    handle_enable_totp_2fa,
    handle_verify_totp_2fa,
    handle_disable_2fa_method,
    handle_remove_trusted_device,
    get_2fa_settings_context,
)

from .utils import (
    handle_login_step_1_credentials as utils_handle_step_1,
    handle_login_step_2_2fa_choice as utils_handle_step_2,
    handle_login_step_3_2fa_verification_logic,
    handle_resend_code_request,
)


# === Project Constants ===
from .constants import (
    EMAIL_CODE_RESEND_DELAY_SECONDS,
    EMAIL_CODE_EXPIRY_SECONDS,
    MAX_2FA_ATTEMPTS,
)

# === Project Logs ===
from logs.utils import log_user_action_json

# =============================================================================
# DECORATORS
# =============================================================================


def redirect_authenticated_user(view_func):
    """
    Decorator to redirect authenticated users away from login/register pages.

    Args:
        view_func: The view function to decorate

    Returns:
        Wrapped function that redirects authenticated users
    """

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapper


def redirect_not_authenticated_user(view_func):
    """
    Decorator to redirect non-authenticated users to login page.

    Args:
        view_func: The view function to decorate

    Returns:
        Wrapped function that redirects non-authenticated users
    """

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper


# =============================================================================
# REGISTRATION VIEWS
# =============================================================================


@redirect_authenticated_user
def register_view(request):
    """
    Main view for the 6-step registration process.

    This view dispatches to the appropriate step handler based on the current step.
    Steps:
    1. Email verification
    2. Email code verification
    3. Personal information
    4. Username selection
    5. Password creation
    6. Account summary and creation
    """
    if request.user.is_authenticated:
        return redirect("profile")

    # Get current step from POST or GET
    if request.method == "POST":
        step = request.POST.get("step", "1")

        # Handle previous button
        if "previous" in request.POST:
            prev_step = str(max(1, int(step) - 1))
            return handle_previous_step(request, prev_step)
    else:
        step = request.GET.get("step", "1")

    # Dispatch to appropriate step handler
    step_handlers = {
        "1": handle_step_1_email,
        "2": handle_step_2_verification,
        "3": handle_step_3_personal_info,
        "4": handle_step_4_username,
        "5": handle_step_5_password,
        "6": handle_step_6_final,
    }

    handler = step_handlers.get(step, handle_step_1_email)
    return handler(request)


@redirect_authenticated_user
def handle_previous_step(request, step):
    """
    Handle navigation to previous step in registration process.

    Args:
        request: HTTP request object
        step: Target step number

    Returns:
        Rendered template for the previous step
    """
    session_data = request.session.get("register_data", {})

    form_classes = {
        "1": RegisterStep1Form,
        "2": RegisterStep2Form,
        "3": RegisterStep3Form,
        "4": RegisterStep4Form,
        "5": RegisterStep5Form,
    }

    FormClass = form_classes.get(step, RegisterStep1Form)
    form = FormClass(initial=session_data)

    return render(
        request,
        "users/register.html",
        {"form": form, "step": step, "progress": int(step) * 100 // 6},
    )


@redirect_authenticated_user
def handle_step_1_email(request):
    """
    Step 1: Email verification.

    User enters email address and receives verification code.
    """
    session_data = request.session.get("register_data", {})

    if request.method == "POST":
        form = RegisterStep1Form(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Check if email is already registered
            if CustomUser.objects.filter(email=email, is_active=True).exists():
                form.add_error("email", "An account with this email already exists.")
            else:
                # Clean up any existing temporary users with this email
                CustomUser.objects.filter(email=email, is_active=False).delete()

                # Generate and send verification code
                verification_code = generate_email_code()

                # Generate a unique temporary username
                import uuid

                temp_username = f"temp_{uuid.uuid4().hex[:8]}"

                # Ensure username uniqueness
                while CustomUser.objects.filter(username=temp_username).exists():
                    temp_username = f"temp_{uuid.uuid4().hex[:8]}"

                # Create temporary user in database for timeout management
                temp_user = CustomUser.objects.create(
                    email=email,
                    username=temp_username,  # Add temporary username
                    first_name="",  # Add empty first_name
                    last_name="",  # Add empty last_name
                    is_active=False,
                    email_verification_code=verification_code,  # Use email_verification_code for registration
                    verification_code_sent_at=timezone.now(),  # Use verification_code_sent_at for registration
                )

                # Store data temporarily
                session_data.update(
                    {
                        "email": email,
                        "verification_code": verification_code,
                        "code_sent_at": timezone.now().isoformat(),
                        "code_attempts": 0,
                    }
                )
                request.session["register_data"] = session_data

                # Send verification email
                success = send_verification_email(email, verification_code)

                if success:
                    messages.success(request, "Verification code sent to your email.")
                    return HttpResponseRedirect(f"{reverse('register')}?step=2")
                else:
                    form.add_error("email", "Error sending email.")
    else:
        form = RegisterStep1Form(initial=session_data)

    return render(
        request, "users/register.html", {"form": form, "step": "1", "progress": 17}
    )


@redirect_authenticated_user
def handle_step_2_verification(request):
    """
    Step 2: Email code verification.

    User enters the verification code received by email.
    """
    session_data = request.session.get("register_data", {})

    if not session_data.get("email"):
        messages.error(request, "Session expired. Please try again.")
        return redirect("register")

    if request.method == "POST":
        form = RegisterStep2Form(request.POST)
        if form.is_valid():
            submitted_code = form.cleaned_data["verification_code"]
            stored_code = session_data.get("verification_code")
            code_sent_at = session_data.get("code_sent_at")
            attempts = session_data.get("code_attempts", 0)

            # Check attempts limit
            if attempts >= 3:
                form.add_error(
                    "verification_code",
                    "Too many attempts. Request a new code.",
                )
            else:
                # Check code expiration (10 minutes)
                if code_sent_at:
                    sent_time = datetime.fromisoformat(
                        code_sent_at.replace("Z", "+00:00")
                        if code_sent_at.endswith("Z")
                        else code_sent_at
                    )
                    if timezone.is_naive(sent_time):
                        sent_time = timezone.make_aware(sent_time)

                    if (
                        timezone.now() - sent_time
                    ).total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:  # 10 minutes
                        form.add_error(
                            "verification_code",
                            "The code has expired. Request a new code.",
                        )
                    elif submitted_code == stored_code:
                        # Code verified successfully - clean up temporary user
                        try:
                            temp_user = CustomUser.objects.get(
                                email=session_data.get("email"), is_active=False
                            )
                            temp_user.delete()
                            print(
                                f"🗑️ Temporary user deleted for email: {session_data.get('email')}"
                            )
                        except CustomUser.DoesNotExist:
                            pass  # User already deleted or doesn't exist

                        session_data["email_verified"] = True
                        request.session["register_data"] = session_data
                        return HttpResponseRedirect(f"{reverse('register')}?step=3")
                    else:
                        attempts += 1
                        session_data["code_attempts"] = attempts
                        request.session["register_data"] = session_data
                        form.add_error(
                            "verification_code",
                            f"Incorrect code. {3-attempts} remaining attempt(s).",
                        )
                else:
                    form.add_error(
                        "verification_code", "Session error. Please try again."
                    )
    else:
        form = RegisterStep2Form()

    # Calculate remaining time for resend using database
    can_resend = True
    time_until_resend = 0

    # Check if we have a temporary user with verification_code_sent_at
    temp_user = None
    try:
        temp_user = CustomUser.objects.get(
            email=session_data.get("email"), is_active=False
        )
        if temp_user.verification_code_sent_at:  # Use correct field
            time_since_sent = timezone.now() - temp_user.verification_code_sent_at

            time_until_resend = max(
                0, EMAIL_CODE_RESEND_DELAY_SECONDS - time_since_sent.total_seconds()
            )
            can_resend = time_until_resend <= 0
    except CustomUser.DoesNotExist:
        pass

    return render(
        request,
        "users/register.html",
        {
            "form": form,
            "step": "2",
            "progress": 33,
            "can_resend": can_resend,
            "time_until_resend": int(time_until_resend),
        },
    )


@redirect_authenticated_user
def handle_step_3_personal_info(request):
    """
    Step 3: Personal information collection.

    User provides first name, last name, and date of birth.
    """
    session_data = request.session.get("register_data", {})

    if not session_data.get("email_verified"):
        messages.error(request, "Please check your email first.")
        return HttpResponseRedirect(f"{reverse('register')}?step=2")

    if request.method == "POST":
        form = RegisterStep3Form(request.POST)
        if form.is_valid():
            # Check minimum age requirement
            birth_date = form.cleaned_data["date_of_birth"]
            age = calculate_age(birth_date)
            MINIMUM_AGE = 16

            if age < MINIMUM_AGE:
                form.add_error(
                    "date_of_birth",
                    f"You must be at least {MINIMUM_AGE} years old to create an account.",
                )
            else:
                session_data.update(
                    {
                        "first_name": form.cleaned_data["first_name"],
                        "last_name": form.cleaned_data["last_name"],
                        "date_of_birth": birth_date.isoformat(),
                    }
                )
                request.session["register_data"] = session_data
                return HttpResponseRedirect(f"{reverse('register')}?step=4")
    else:
        form = RegisterStep3Form(initial=session_data)

    return render(
        request, "users/register.html", {"form": form, "step": "3", "progress": 50}
    )


@redirect_authenticated_user
def handle_step_4_username(request):
    """
    Step 4: Username selection.

    User chooses a unique username for their account.
    """
    session_data = request.session.get("register_data", {})

    if not session_data.get("first_name"):
        messages.error(request, "Please complete the previous steps.")
        return HttpResponseRedirect(f"{reverse('register')}?step=3")

    if request.method == "POST":
        if request.POST.get("check_username"):
            # AJAX username verification
            username = request.POST.get("username", "").strip()
            is_available = not CustomUser.objects.filter(username=username).exists()
            return JsonResponse({"available": is_available})

        form = RegisterStep4Form(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]

            if CustomUser.objects.filter(username=username).exists():
                form.add_error("username", "This username is already taken.")
            else:
                session_data["username"] = username
                request.session["register_data"] = session_data
                return HttpResponseRedirect(f"{reverse('register')}?step=5")
    else:
        form = RegisterStep4Form(initial=session_data)

    return render(
        request, "users/register.html", {"form": form, "step": "4", "progress": 67}
    )


@redirect_authenticated_user
def handle_step_5_password(request):
    """
    Step 5: Password creation.

    User creates and confirms their password.
    """
    session_data = request.session.get("register_data", {})

    if not session_data.get("username"):
        messages.error(request, "Please complete the previous steps.")
        return HttpResponseRedirect(f"{reverse('register')}?step=4")

    if request.method == "POST":
        form = RegisterStep5Form(request.POST)
        if form.is_valid():
            session_data.update(
                {
                    "password1": form.cleaned_data["password1"],
                    "password2": form.cleaned_data["password2"],
                }
            )
            request.session["register_data"] = session_data
            return HttpResponseRedirect(f"{reverse('register')}?step=6")
    else:
        form = RegisterStep5Form()

    return render(
        request, "users/register.html", {"form": form, "step": "5", "progress": 83}
    )


@redirect_authenticated_user
def handle_step_6_final(request):
    """
    Step 6: Account summary and creation.

    User reviews their information and creates their account.
    """
    session_data = request.session.get("register_data", {})

    if not session_data.get("password1"):
        messages.error(request, "Please complete the previous steps.")
        return HttpResponseRedirect(f"{reverse('register')}?step=5")

    if request.method == "POST":
        # Create the user account
        try:
            # Validate required session data
            required_fields = [
                "email",
                "username",
                "first_name",
                "last_name",
                "date_of_birth",
                "password1",
            ]
            missing_fields = [
                field for field in required_fields if not session_data.get(field)
            ]

            if missing_fields:
                messages.error(
                    request,
                    f"Missing required data: {', '.join(missing_fields)}. Please complete all steps.",
                )
                return HttpResponseRedirect(f"{reverse('register')}?step=1")

            # Validate date format
            try:
                date_of_birth = date.fromisoformat(session_data["date_of_birth"])
            except ValueError as e:
                messages.error(
                    request, f"Invalid date format: {session_data['date_of_birth']}"
                )
                return HttpResponseRedirect(f"{reverse('register')}?step=3")

            # Check if user already exists
            if CustomUser.objects.filter(email=session_data["email"]).exists():
                messages.error(request, "An account with this email already exists.")
                return HttpResponseRedirect(f"{reverse('register')}?step=1")

            if CustomUser.objects.filter(username=session_data["username"]).exists():
                messages.error(request, "This username is already taken.")
                return HttpResponseRedirect(f"{reverse('register')}?step=4")

            # Create the user
            user = CustomUser(
                email=session_data["email"],
                username=session_data["username"],
                first_name=session_data["first_name"],
                last_name=session_data["last_name"],
                date_of_birth=date_of_birth,
                is_email_verified=True,  # Already verified at step 2
            )
            user.set_password(session_data["password1"])

            # Log user creation
            ip = get_client_ip(request)
            user.ip_address = ip
            user.save()

            log_user_action_json(
                user=user,
                action="register",
                request=request,
                ip_address=ip,
                extra_info={"impacted_user_id": user.id},
            )

            # Clean session data
            request.session.pop("register_data", None)

            # Automatically log in user
            user.backend = (
                f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
            )
            login(request, user)

            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()

            messages.success(
                request, f"Account created successfully! Welcome {user.first_name}"
            )
            return redirect("profile")

        except Exception as e:
            # Log the detailed error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error creating account: {str(e)}", exc_info=True)

            # Provide more specific error messages
            if (
                "UNIQUE constraint failed" in str(e)
                or "duplicate key" in str(e).lower()
            ):
                if "email" in str(e).lower():
                    messages.error(
                        request, "An account with this email already exists."
                    )
                elif "username" in str(e).lower():
                    messages.error(request, "This username is already taken.")
                else:
                    messages.error(
                        request,
                        "Account creation failed due to duplicate data. Please try again.",
                    )
            elif "NOT NULL constraint failed" in str(e):
                messages.error(
                    request, "Missing required information. Please complete all steps."
                )
            elif "database" in str(e).lower() or "connection" in str(e).lower():
                messages.error(
                    request, "Database connection error. Please try again later."
                )
            else:
                messages.error(
                    request, f"Error creating account: {str(e)}. Please try again."
                )

            return HttpResponseRedirect(f"{reverse('register')}?step=5")

    return render(
        request,
        "users/register.html",
        {
            "form": None,
            "step": "6",
            "progress": 100,
            "session_data": session_data,
        },
    )


@redirect_authenticated_user
def resend_verification_code_view(request):
    """
    View to resend verification code for registration.

    Handles POST requests to resend verification codes with proper timing controls.
    """
    if request.method != "POST":
        return HttpResponseRedirect(f"{reverse('register')}?step=2")

    session_data = request.session.get("register_data", {})
    email = session_data.get("email")

    if not email:
        messages.error(request, "Session expired.")
        return redirect("register")

    # Check timing using database instead of session
    can_resend = True
    try:
        temp_user = CustomUser.objects.get(email=email, is_active=False)
        if temp_user.verification_code_sent_at:  # Use correct field
            delta = timezone.now() - temp_user.verification_code_sent_at

            if delta.total_seconds() < EMAIL_CODE_RESEND_DELAY_SECONDS:
                messages.error(request, "Please wait before requesting a new code.")
                return HttpResponseRedirect(f"{reverse('register')}?step=2")
    except CustomUser.DoesNotExist:
        pass

    # Generate and send new code
    new_code = generate_email_code()

    # Update both session and database
    session_data.update(
        {
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        }
    )
    request.session["register_data"] = session_data

    # Delete old temporary user and create new one
    try:
        old_temp_user = CustomUser.objects.get(email=email, is_active=False)
        old_temp_user.delete()
        print(f"🗑️ Old temporary user deleted for resend: {email}")
    except CustomUser.DoesNotExist:
        pass

    # Create new temporary user with new code
    import uuid

    temp_username = f"temp_{uuid.uuid4().hex[:8]}"
    while CustomUser.objects.filter(username=temp_username).exists():
        temp_username = f"temp_{uuid.uuid4().hex[:8]}"

    temp_user = CustomUser.objects.create(
        email=email,
        username=temp_username,
        first_name="",
        last_name="",
        is_active=False,
        email_verification_code=new_code,
        verification_code_sent_at=timezone.now(),
    )

    if send_verification_email(email, new_code):
        messages.success(request, "New code sent.")
    else:
        messages.error(request, "Error sending code.")

    return HttpResponseRedirect(f"{reverse('register')}?step=2")


# ========= AJAX VIEWS =========
@csrf_exempt
@require_POST
def check_username_availability(request):
    """
    AJAX view to check username availability in real time.

    Returns JSON response with availability status and message.
    """
    username = request.POST.get("username", "").strip()

    if not username:
        return JsonResponse({"available": False, "message": "Username required"})

    if len(username) < 3:
        return JsonResponse({"available": False, "message": "Minimum 3 characters"})

    # Check allowed characters
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return JsonResponse(
            {"available": False, "message": "Only letters, numbers and _ allowed"}
        )

    # Check availability
    is_available = not CustomUser.objects.filter(username=username).exists()

    return JsonResponse(
        {
            "available": is_available,
            "message": "Available" if is_available else "Already taken",
        }
    )


# =============================================================================
# LOGIN VIEWS
# =============================================================================


@redirect_authenticated_user
def login_view(request):
    """
    Main view for the 3-step login process.

    This view dispatches to the appropriate step handler based on the current step.
    Steps:
    1. Credentials validation (email/username + password)
    2. 2FA method choice (if both methods enabled)
    3. 2FA verification (email code or TOTP)
    """
    if request.user.is_authenticated:
        return redirect("profile")

    # Get current step from POST or GET
    if request.method == "POST":
        step = request.POST.get("step", "login")

        # Handle previous button
        if "previous" in request.POST:
            prev_step = get_previous_login_step(step)
            return handle_previous_login_step(request, prev_step)
    else:
        step = request.GET.get("step", "login")

    # Dispatch to appropriate step handler
    step_handlers = {
        "login": handle_login_step_1_credentials,
        "choose_2fa": handle_login_step_2_2fa_choice,
        "email_2fa": handle_login_step_3_2fa_verification,
        "totp_2fa": handle_login_step_3_2fa_verification,
    }

    handler = step_handlers.get(step, handle_login_step_1_credentials)
    return handler(request)


@redirect_authenticated_user
def handle_previous_login_step(request, step):
    """
    Handle navigation to previous step in login process.

    Args:
        request: HTTP request object
        step: Target step name

    Returns:
        Rendered template for the previous step
    """
    session_data = request.session.get("login_data", {})

    form_classes = {
        "login": LoginForm,
        "choose_2fa": Choose2FAMethodForm,
        "email_2fa": Email2FAForm,
        "totp_2fa": TOTP2FAForm,
    }

    FormClass = form_classes.get(step, LoginForm)
    form = FormClass(initial=session_data)

    return render(
        request,
        "users/login.html",
        {
            "form": form,
            "step": step,
            "progress": get_login_step_progress(step),
            "user": get_user_from_session(request) if step != "login" else None,
            "can_resend": (
                can_resend_code(session_data)
                if step in ["email_2fa", "totp_2fa"]
                else None
            ),
            "time_until_resend": (
                _calculate_time_until_resend(session_data)
                if step in ["email_2fa", "totp_2fa"]
                else 0
            ),
        },
    )


@redirect_authenticated_user
def handle_login_step_1_credentials(request):
    """
    Step 1: Credentials validation.

    User enters email/username and password for authentication.
    """
    if request.method == "POST":
        success, user, error_message = utils_handle_step_1(request)

        if success:
            # Check if 2FA is required
            if user.email_2fa_enabled or user.totp_enabled:
                # Check if this is a trusted device
                if is_trusted_device(request, user):
                    # Trusted device - proceed directly to login
                    return handle_login_success(request, user)

                # Not a trusted device - proceed with 2FA
                # Initialize session data
                initialize_login_session_data(request, user)

                # If both methods are enabled, go to choice step
                if user.email_2fa_enabled and user.totp_enabled:
                    return HttpResponseRedirect(f"{reverse('login')}?step=choose_2fa")

                # If only email 2FA is enabled
                elif user.email_2fa_enabled:
                    code = generate_email_code()
                    user.email_2fa_code = code
                    user.email_2fa_sent_at = timezone.now()
                    user.save()

                    # Initialize session data and set the chosen 2FA method
                    session_data = initialize_login_session_data(request, user, code)
                    session_data["chosen_2fa_method"] = "email"
                    request.session["login_data"] = session_data

                    success = send_2FA_email(user, code)

                    if success:
                        messages.success(
                            request,
                            "A verification code has been sent to your email address.",
                        )
                    else:
                        messages.error(request, "Error sending verification code.")

                    return HttpResponseRedirect(f"{reverse('login')}?step=email_2fa")

                # If only TOTP is enabled
                elif user.totp_enabled:
                    # Initialize session data and set the chosen 2FA method
                    session_data = initialize_login_session_data(request, user)
                    session_data["chosen_2fa_method"] = "totp"
                    request.session["login_data"] = session_data

                    return HttpResponseRedirect(f"{reverse('login')}?step=totp_2fa")

            # No 2FA required, proceed to login
            return handle_login_success(request, user)
        else:
            form = LoginForm(request.POST)
            form.add_error("email", error_message)
            messages.error(request, error_message)
    else:
        form = LoginForm()

    return render(
        request,
        "users/login.html",
        {"form": form, "step": "login", "progress": get_login_step_progress("login")},
    )


@redirect_authenticated_user
def handle_login_step_2_2fa_choice(request):
    """
    Step 2: 2FA method choice.

    User chooses between email and TOTP 2FA methods (if both enabled).
    """
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")

    if not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect("login")

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    if request.method == "POST":
        success, user, error_message = utils_handle_step_2(request)

        if success:
            method = request.POST.get("twofa_method")

            if method == "email":
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()

                session_data = request.session.get("login_data", {})
                session_data.update(
                    {
                        "verification_code": code,
                        "code_sent_at": timezone.now().isoformat(),
                        "code_attempts": 0,
                    }
                )
                request.session["login_data"] = session_data

                success = send_2FA_email(user, code)
                if success:
                    messages.success(request, "Verification code sent to your email.")
                else:
                    messages.error(request, "Error sending verification code.")

                return HttpResponseRedirect(f"{reverse('login')}?step=email_2fa")

            elif method == "totp":
                return HttpResponseRedirect(f"{reverse('login')}?step=totp_2fa")
        else:
            form = Choose2FAMethodForm(request.POST)
            form.add_error("twofa_method", error_message)
            messages.error(request, error_message)
    else:
        form = Choose2FAMethodForm()

    return render(
        request,
        "users/login.html",
        {
            "form": form,
            "step": "choose_2fa",
            "progress": get_login_step_progress("choose_2fa"),
            "user": user,
        },
    )


@redirect_authenticated_user
def handle_login_step_3_2fa_verification(request):
    """
    Step 3: 2FA verification.

    User enters verification code (email or TOTP) to complete login.
    """
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    chosen_method = session_data.get("chosen_2fa_method")

    if not user_id:
        messages.error(request, "Session expired. Please try again.")
        return redirect("login")

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # Handle resend code request
    if request.method == "POST" and request.POST.get("resend_code"):
        success, message = handle_resend_code_request(
            request, session_data, user, "email"
        )

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        # Return to the same step with updated form
        FormClass = Email2FAForm if chosen_method == "email" else TOTP2FAForm
        form = FormClass()

        return render(
            request,
            "users/login.html",
            {
                "form": form,
                "step": "email_2fa" if chosen_method == "email" else "totp_2fa",
                "progress": get_login_step_progress(
                    "email_2fa" if chosen_method == "email" else "totp_2fa"
                ),
                "user": user,
                "can_resend": can_resend_code(session_data),
                "time_until_resend": _calculate_time_until_resend(session_data),
                "email_code_resend_delay": EMAIL_CODE_RESEND_DELAY_SECONDS,
            },
        )

    if request.method == "POST":
        success, user, error_message = handle_login_step_3_2fa_verification_logic(
            request
        )

        if success:
            return handle_login_success(request, user)
        else:
            FormClass = Email2FAForm if chosen_method == "email" else TOTP2FAForm
            form = FormClass(request.POST)
            form.add_error("twofa_code", error_message)
            messages.error(request, error_message)
    else:
        FormClass = Email2FAForm if chosen_method == "email" else TOTP2FAForm
        form = FormClass()

    return render(
        request,
        "users/login.html",
        {
            "form": form,
            "step": "email_2fa" if chosen_method == "email" else "totp_2fa",
            "progress": get_login_step_progress(
                "email_2fa" if chosen_method == "email" else "totp_2fa"
            ),
            "user": user,
            "can_resend": can_resend_code(session_data),
            "time_until_resend": _calculate_time_until_resend(session_data),
            "email_code_resend_delay": EMAIL_CODE_RESEND_DELAY_SECONDS,
        },
    )


def handle_login_success(request, user):
    """
    Handle successful login completion.

    Args:
        request: HTTP request object
        user: Authenticated user object

    Returns:
        Redirect to appropriate page after successful login
    """
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_location_from_ip(ip)
    remember_device = request.session.get("remember_device", False)

    # Handle remember device setting
    if remember_device:
        request.session.set_expiry(1209600)  # 2 weeks
    else:
        request.session.set_expiry(0)  # Session expires when browser closes

    # Check if it's a trusted device
    if (user.email_2fa_enabled or user.totp_enabled) and is_trusted_device(
        request, user
    ):
        return login_success(
            request,
            user,
            ip,
            user_agent,
            location,
            twofa_method="trusted_device",
            remember_device=remember_device,
        )

    # Regular login success
    return login_success(
        request=request,
        user=user,
        ip=ip,
        user_agent=user_agent,
        location=location,
        twofa_method=None,
        remember_device=remember_device,
    )


def get_previous_login_step(current_step):
    """
    Get the previous step in the login process.

    Args:
        current_step: Current step name

    Returns:
        Previous step name
    """
    step_sequence = {
        "choose_2fa": "login",
        "email_2fa": "choose_2fa",
        "totp_2fa": "choose_2fa",
    }
    return step_sequence.get(current_step, "login")


# =============================================================================
# LOGOUT VIEWS
# =============================================================================


def logout_view(request):
    """
    Handle user logout.

    Logs the logout action and redirects to login page.
    """
    if request.user.is_authenticated:
        user = request.user
        user.is_online = False
        user.save()

        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        location = get_location_from_ip(ip)
        log_user_action_json(
            user=user,
            action="logout",
            request=request,
            extra_info={
                "impacted_user_id": user.id,
            },
        )

    logout(request)
    return redirect("login")


# =============================================================================
# ACCOUNT MANAGEMENT VIEWS
# =============================================================================


@redirect_not_authenticated_user
def profile_view(request):
    """
    User profile management view.

    Allows users to view and update their profile information.
    """
    user = request.user
    if request.method == "POST":
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_data = CustomUser.objects.get(pk=user.pk)

            # Handle profile picture deletion
            if form.cleaned_data.get("profile_picture") and old_data.profile_picture:
                schedule_profile_picture_deletion(old_data.profile_picture.path)

            form.save()

            # Log profile update
            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            location = get_location_from_ip(ip)

            changes = get_changes_dict(old_data, user, form.changed_data)
            log_user_action_json(
                user=user,
                action="profile_update",
                request=request,
                ip_address=ip,
                extra_info={
                    "impacted_user_id": user.id,
                    "changes": changes,
                },
            )

            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = CustomUserUpdateForm(instance=user)

    return render(
        request,
        "users/profile.html",
        {
            "form": form,
            "user": user,
        },
    )


@redirect_not_authenticated_user
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    """
    Account deletion view.

    Handles account deletion with confirmation and logging.
    """
    user = request.user

    if request.method == "POST":
        password = request.POST.get("password")
        if user.check_password(password):
            # Log account deletion
            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            location = get_location_from_ip(ip)

            log_user_action_json(
                user=user,
                action="account_deletion",
                request=request,
                ip_address=ip,
                extra_info={
                    "impacted_user_id": user.id,
                },
            )

            # Delete the user account
            user.delete()
            logout(request)
            messages.success(request, "Your account has been deleted successfully.")
            return redirect("login")
        else:
            messages.error(request, "Incorrect password.")
            return render(request, "users/delete_account_confirm.html")

    return render(request, "users/delete_account_confirm.html")


# =============================================================================
# 2FA SETTINGS VIEWS
# =============================================================================


@redirect_not_authenticated_user
def twofa_settings_view(request):
    """
    2FA settings management view.

    Allows users to enable/disable 2FA methods and manage trusted devices.
    """
    user = request.user
    trusted_devices = TrustedDevice.objects.filter(user=user).order_by("-created_at")
    step = request.GET.get("step", "initial")

    # Get current device token and enhance device information
    current_device_token = get_current_device_token(request, user)
    for device in trusted_devices:
        enhance_trusted_device_info(device, current_device_token)

    # Get base context
    context = get_2fa_settings_context(user, trusted_devices, step)

    if request.method == "POST":
        action = request.POST.get("action")

        # Handle different actions
        if action == "cancel":
            return handle_2fa_cancel_operation(user, step)

        elif action == "enable_email":
            return handle_enable_email_2fa_action(request, user)

        elif action == "verify_email_code":
            return handle_verify_email_2fa_action(request, user)

        elif action == "resend_email_code":
            return handle_resend_email_2fa_action(request, user)

        elif action == "enable_totp":
            return handle_enable_totp_2fa_action(request, user, context)

        elif action == "verify_totp":
            return handle_verify_totp_2fa_action(request, user)

        elif action == "disable_email":
            return handle_disable_2fa_action(request, user, "email")

        elif action == "disable_totp":
            return handle_disable_2fa_action(request, user, "totp")

        elif action in ["remove_trusted_device", "revoke_device"]:
            return handle_remove_trusted_device_action(
                request, user, current_device_token
            )

    return render(request, "users/2fa_settings.html", context)


def handle_enable_email_2fa_action(request, user):
    """Handle enabling email 2FA action."""
    password = request.POST.get("password")
    success, redirect_url, error_message = handle_enable_email_2fa(user, password)

    if not success:
        messages.error(request, error_message)
        return redirect("twofa_settings")

    return redirect(redirect_url)


def handle_verify_email_2fa_action(request, user):
    """Handle email 2FA verification action."""
    code = request.POST.get("email_code")
    success, error_message = handle_verify_email_2fa(user, code)

    if success:
        messages.success(request, "Email 2FA enabled successfully!")
        return redirect(reverse("twofa_settings") + "?step=initial")
    else:
        messages.error(request, error_message)
        return redirect(reverse("twofa_settings") + "?step=verify_email_code")


def handle_resend_email_2fa_action(request, user):
    """Handle resending email 2FA code action."""
    success, redirect_url, error_message = handle_resend_email_2fa_code(user)

    if success:
        messages.success(
            request, error_message
        )  # error_message contains success message here
    else:
        messages.error(request, error_message)

    url = reverse("twofa_settings") + "?" + urlencode({"step": "verify_email_code"})
    return redirect(url)


def handle_enable_totp_2fa_action(request, user, context):
    """Handle enabling TOTP 2FA action."""
    password = request.POST.get("password")
    success, context_data, error_message = handle_enable_totp_2fa(user, password)

    if not success:
        messages.error(request, error_message)
        return redirect("twofa_settings")

    # Update context with TOTP data
    context.update(context_data)
    return render(request, "users/2fa_settings.html", context)


def handle_verify_totp_2fa_action(request, user):
    """Handle TOTP 2FA verification action."""
    code = request.POST.get("totp_code")  # Changed from "code" to "totp_code"
    success, error_message = handle_verify_totp_2fa(user, code)

    if success:
        messages.success(request, "TOTP 2FA enabled successfully!")
        return redirect(reverse("twofa_settings") + "?step=initial")
    else:
        messages.error(request, error_message)
        return redirect(reverse("twofa_settings") + "?step=verify_totp")


def handle_disable_2fa_action(request, user, method):
    """Handle disabling 2FA methods action."""
    password = request.POST.get("password")
    success, message = handle_disable_2fa_method(user, password, method)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect("twofa_settings")


def handle_remove_trusted_device_action(request, user, current_device_token):
    """Handle removing trusted device action."""
    device_id = request.POST.get("device_id") or request.POST.get("revoke_device_id")
    success, is_current_device, error_message = handle_remove_trusted_device(
        user, device_id, current_device_token
    )

    if not success:
        messages.error(request, error_message)
        return redirect("twofa_settings")

    if is_current_device:
        response = redirect("twofa_settings")
        response.delete_cookie(f"trusted_device_{user.pk}")
        messages.success(request, "Current trusted device removed successfully!")
        return response
    else:
        messages.success(request, "Trusted device removed successfully!")
        return redirect("twofa_settings")


# ========= AJAX VIEWS =========


@csrf_exempt
@require_POST
def resend_2fa_code_view(request):
    """
    AJAX view to resend 2FA code.

    Handles POST requests to resend 2FA codes with proper timing controls.
    """
    session_data = request.session.get("login_data", {})
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    user = get_user_from_session(request)
    if not user:
        return JsonResponse({"error": "Session expired."}, status=401)

    if not can_resend_code(session_data):
        messages.warning(request, "Wait 2 minutes before requesting a new code.")
        return JsonResponse(
            {"error": "Cannot resend code within 2 minutes."}, status=403
        )

    new_code = generate_email_code()
    session_data.update(
        {
            "2fa_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
        }
    )
    request.session["login_data"] = session_data

    if send_2FA_email(user, new_code):
        return JsonResponse({"success": True, "message": "New code sent successfully."})
    else:
        return JsonResponse(
            {"success": False, "message": "Error sending code."}, status=500
        )
