# Context: Django user management views with detailed JSON logging.

# === Python Standard Library ===
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
import re

# === Django Imports ===
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_backends, login, logout
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
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

# === Project users/utils ===
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
    generate_email_code,
    send_verification_email,
    verify_totp,
    get_changes_dict,
    get_user_agent,
    get_client_ip,
    hash_token,
    get_user_from_session,
    send_2FA_email,
    initialize_2fa_session_data,
)

# === Project logs/utils ===
from logs.utils import log_user_action_json


# ========= DECORATORS =========
def redirect_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return wrapper


def redirect_not_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper


# ================ VIEWS ================ #


# ------==== Registration Views ===------- #
@redirect_authenticated_user
def register_view(request):
    "Main view for the 6-step registration process"
    if request.user.is_authenticated:
        return redirect("profile")

    # Retrieve the current step
    if request.method == "POST":
        step = request.POST.get("step", "1")

        # Previous button management
        if "previous" in request.POST:
            prev_step = str(max(1, int(step) - 1))
            return handle_previous_step(request, prev_step)
    else:
        step = request.GET.get("step", "1")

    # Dispatch to the appropriate function
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
    """Management of return to the previous step"""
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
    """Step 1: Enter email and generate code"""
    session_data = request.session.get("register_data", {})

    if request.method == "POST":
        form = RegisterStep1Form(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # Check if email is alredy registered
            if CustomUser.objects.filter(email=email).exists():
                form.add_error("email", "An account with this email already exists.")
            else:
                # Generate and send the verification code
                verification_code = generate_email_code()

                # Temporarily store data
                session_data.update(
                    {
                        "email": email,
                        "verification_code": verification_code,
                        "code_sent_at": timezone.now().isoformat(),
                        "code_attempts": 0,
                    }
                )
                request.session["register_data"] = session_data

                # Send email
                # TODO: Personalize the email
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
    """ "Step 2: Verify Email Code"""
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

            # Vérifier les tentatives
            if attempts >= 3:
                form.add_error(
                    "verification_code",
                    "Too many attempts. Request a new code.",
                    # TODO: Send email notification to email adress if too many attempts to prevent person that someone tries to create an account with this email adress
                )
            else:
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
                        form.add_error(
                            "verification_code",
                            "LThe code has expired. Request a new code.",
                        )
                    elif submitted_code == stored_code:
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

    # Calculer le temps restant pour renvoyer le code
    can_resend = can_resend_code(session_data)

    return render(
        request,
        "users/register.html",
        {
            "form": form,
            "step": "2",
            "progress": 33,
            "email": session_data.get("email"),
            "can_resend": can_resend,
        },
    )


@redirect_authenticated_user
def handle_step_3_personal_info(request):
    """Step 3: First name, last name and date of birth"""
    session_data = request.session.get("register_data", {})

    if not session_data.get("email_verified"):
        messages.error(request, "Please check your email first.")
        return HttpResponseRedirect(f"{reverse('register')}?step=2")

    if request.method == "POST":
        form = RegisterStep3Form(request.POST)
        if form.is_valid():
            # Check minimum age
            birth_date = form.cleaned_data["date_of_birth"]
            age = calculate_age(birth_date)
            MINIMUM_AGE = 16
            if age < MINIMUM_AGE:
                form.add_error(
                    "date_of_birth",
                    f"You must be at least { age } years old to create an account.",
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
    """Step 4: Choosing a Username"""
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
    """Step 5: Password and Confirmation"""
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
    """Step 6: Summary and account creation"""
    session_data = request.session.get("register_data", {})

    if not session_data.get("password1"):
        messages.error(request, "Please complete the previous steps.")
        return HttpResponseRedirect(f"{reverse('register')}?step=5")

    if request.method == "POST":
        # Create the user account
        try:
            date_of_birth = date.fromisoformat(session_data["date_of_birth"])

            user = CustomUser(
                email=session_data["email"],
                username=session_data["username"],
                first_name=session_data["first_name"],
                last_name=session_data["last_name"],
                date_of_birth=date_of_birth,
                is_email_verified=True,  # Already verify at step 2
            )
            user.set_password(session_data["password1"])

            # Log
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

            # Clean session
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
            messages.error(request, "Error creating account. Please try again.")
            return HttpResponseRedirect(f"{reverse('register')}?step=5")

    return render(
        request,
        "users/register.html",
        {"step": "6", "progress": 100, "session_data": session_data, "summary": True},
    )


@redirect_authenticated_user
def resend_verification_code_view(request):
    """View to return verification code"""
    if request.method != "POST":
        return HttpResponseRedirect(f"{reverse('register')}?step=2")

    session_data = request.session.get("register_data", {})
    email = session_data.get("email")

    if not email:
        messages.error(request, "Session expired.")
        return redirect("register")

    if not can_resend_code(session_data):
        messages.warning(request, "Wait 2 minutes before requesting a new code.")
        return HttpResponseRedirect(f"{reverse('register')}?step=2")

    # Generate and send a new code
    new_code = generate_email_code()
    session_data.update(
        {
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        }
    )
    request.session["register_data"] = session_data

    if send_verification_email(email, new_code):
        messages.success(request, "New code sent.")
    else:
        messages.error(request, "Error sending.")

    return HttpResponseRedirect(f"{reverse('register')}?step=2")


# ----- Ajax ----- #
@csrf_exempt
@require_POST
def check_username_availability(request):
    """AJAX view to check username availability in real time"""
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

    # Check disponibility
    is_available = not CustomUser.objects.filter(username=username).exists()

    return JsonResponse(
        {
            "available": is_available,
            "message": "Available" if is_available else "Already taken",
        }
    )


# ------==== Logout View ====------- #
def logout_view(request):
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


# ========== CUSTOMIZATION VIEWS
# ------==== Profile View ====------- #
@redirect_not_authenticated_user
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_data = CustomUser.objects.get(pk=user.pk)

            # Save old photo for delayed deletion
            old_profile_picture = None
            if "profile_picture" in form.changed_data and old_data.profile_picture:
                old_profile_picture = old_data.profile_picture.name

            updated_user = form.save()

            # Delete the old photo later
            if old_profile_picture:
                delay = getattr(
                    settings, "PROFILE_PICTURE_DELETION_DELAY_SECONDS", 86400
                )
                schedule_profile_picture_deletion(old_profile_picture, seconds=delay)

            changes_dict = get_changes_dict(old_data, updated_user, form.changed_data)

            log_user_action_json(
                user=user,
                action="update_profile",
                request=request,
                extra_info={
                    "impacted_user_id": user.id,
                    "changes": changes_dict,
                },
            )
            return redirect("profile")
        else:
            return render(request, "users/profile.html", {"form": form})

    else:
        form = CustomUserUpdateForm(instance=user)
        return render(request, "users/profile.html", {"form": form})


# ------==== Delete user View ====------- #
@redirect_not_authenticated_user
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    user = request.user
    if user.is_superuser:
        messages.error(request, "A superuser can delete its account there.")
        return redirect("profile")

    if request.method == "POST":
        action = request.POST.get("action")
        password = request.POST.get("password", "")

        if not user.check_password(password):
            messages.error(request, "Incorrect password.")
            return redirect("delete_account")

        ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        if action == "anonymize":
            user.anonymize()
            log_user_action_json(
                user=user,
                action="anonymize",
                request=request,
            )
            logout(request)
            messages.success(
                request, "Your account has been anonymized and deactivated."
            )
            return redirect("home")

        elif action == "delete":
            with transaction.atomic():
                user_to_delete = user
                logout(request)
                log_user_action_json(
                    user=user,
                    action="delete_account",
                    request=request,
                )
                user_to_delete.delete()
            messages.success(request, "Votre compte a été supprimé définitivement.")
            return redirect("login")
        else:
            messages.error(request, "Invalid action.")
            return redirect("delete_account")

    # Display related object warnings
    related_warnings = []
    for rel in user._meta.get_fields():
        if (
            (rel.one_to_many or rel.one_to_one)
            and rel.auto_created
            and not rel.concrete
        ):
            accessor = rel.get_accessor_name()
            try:
                if rel.one_to_many:
                    qs = getattr(user, accessor).all()
                    count = qs.count()
                else:
                    obj = getattr(user, accessor, None)
                    count = 1 if obj else 0
                if count:
                    model_verbose = rel.related_model._meta.verbose_name_plural.title()
                    related_warnings.append(
                        {
                            "model": model_verbose,
                            "count": count,
                        }
                    )
            except Exception:
                pass

    return render(
        request,
        "users/delete_account_confirm.html",
        {"related_warnings": related_warnings},
    )


# ------==== Two FA settings View ====------- #
@redirect_not_authenticated_user
def twofa_settings_view(request):
    user = request.user

    # Delete expired devices
    user.trusted_devices.filter(expires_at__lte=timezone.now()).delete()

    trusted_devices = user.trusted_devices.filter(
        expires_at__gt=timezone.now()
    ).order_by("-last_used_at")

    cookie_token = request.COOKIES.get(f"trusted_device_{user.pk}")

    EMAIL_CODE_RESEND_DELAY_SECONDS = 20

    for device in trusted_devices:
        ua_info = analyze_user_agent(device.user_agent)
        device.device_type = ua_info["device_type"]
        device.device_family = ua_info["device_family"]
        device.browser_family = ua_info["browser_family"]
        device.browser_version = ua_info["browser_version"]
        device.os_family = ua_info["os_family"]
        device.os_version = ua_info["os_version"]
        device.is_current_device = (
            device.device_token == hash_token(cookie_token) if cookie_token else False
        )
        print(device.device_token, request.COOKIES.get(f"trusted_device_{user.pk}"))

        expiration_duration = timedelta(days=30)
        device.expires_at = device.last_used_at + expiration_duration
        device.expires_soon = (device.expires_at - timezone.now()) < timedelta(days=7)

        if device.expires_at:
            device.expires_soon = device.expires_at <= timezone.now() + timedelta(
                days=5
            )
        else:
            device.expires_soon = False

    context = {
        "trusted_devices": trusted_devices,
    }

    # Calculating the time before being able to resend an email code
    if user.email_2fa_sent_at:
        delta = timezone.now() - user.email_2fa_sent_at
        time_until_resend = max(
            0, EMAIL_CODE_RESEND_DELAY_SECONDS - int(delta.total_seconds())
        )
        can_resend = time_until_resend <= 0
    else:
        time_until_resend = 0
        can_resend = True

    context = {
        "trusted_devices": trusted_devices,
        "email_2fa_enabled": user.email_2fa_enabled,
        "totp_enabled": user.totp_enabled,
        "time_until_resend": time_until_resend,
        "can_resend": can_resend,
    }

    step = request.GET.get("step", "initial")
    context["step"] = step

    if request.method == "POST":
        action = request.POST.get("action")

        # Cancel an operation in progress
        if action == "cancel":
            # Deletes the email and totp code session if in progress
            if step == "verify_email_code":
                user.email_2fa_code = ""
                user.email_2fa_sent_at = None
                user.save()
            elif step == "verify_totp":
                user.twofa_totp_secret = ""
                user.save()

            # Possible deletion of the remember_device cookie
            response = redirect(reverse("twofa_settings") + "?step=initial")
            response.delete_cookie("remember_device")
            return response

        # 2FA activation by email (sending the code)
        elif action == "enable_email":
            password = request.POST.get("password")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
            else:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()
                generate_email_code(user, code)
                url = (
                    reverse("twofa_settings")
                    + "?"
                    + urlencode({"step": "verify_email_code"})
                )
                return redirect(url)

        # Email code verification
        elif action == "verify_email_code":
            input_code = request.POST.get("email_code")
            if is_email_code_valid(user, input_code):
                user.email_2fa_enabled = True
                user.email_2fa_code = ""
                user.save()
                log_user_action_json(
                    user=user,
                    action="enable_email_2fa",
                    request=request,
                )
                messages.success(request, "2FA par e-mail activée.")
                return redirect("twofa_settings")
            else:
                messages.error(request, "Code invalide ou expiré.")
                url = (
                    reverse("twofa_settings")
                    + "?"
                    + urlencode({"step": "verify_email_code"})
                )
                return redirect(url)

        # Email deactigation

        elif action == "disable_email":
            password = request.POST.get("password")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
                return redirect("twofa_settings")
            else:
                user.email_2fa_enabled = False
                user.email_2fa_code = ""
                user.save()
                log_user_action_json(
                    user=user,
                    action="disable_email_2fa",
                    request=request,
                )
                messages.success(request, "Authentification par e-mail désactivée.")
                return redirect("twofa_settings")

        # Resend email code
        elif action == "resend_email_code":
            delta = (
                (timezone.now() - user.email_2fa_sent_at)
                if user.email_2fa_sent_at
                else timedelta(minutes=999)
            )
            if delta.total_seconds() >= EMAIL_CODE_RESEND_DELAY_SECONDS:
                user.email_2fa_code = generate_email_code()
                user.email_2fa_sent_at = timezone.now()
                user.save()
                generate_email_code(user, user.email_2fa_code)
                messages.success(request, "New code sent.")
            else:
                messages.error(request, "Please wait before requesting a new code.")

            url = (
                reverse("twofa_settings")
                + "?"
                + urlencode({"step": "verify_email_code"})
            )
            return redirect(url)

        # TOTP activation (secret link and QR code generation)
        elif action == "enable_totp":
            password = request.POST.get("password")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
            else:
                secret = generate_totp_secret()
                user.twofa_totp_secret = secret
                user.save()

                uri = get_totp_uri(user, secret)
                qr_base64 = generate_qr_code_base64(uri)

                context.update(
                    {
                        "qr_code_url": qr_base64,
                        "totp_secret": secret,
                        "totp_uri": uri,
                        "step": "verify_totp",
                    }
                )
                return render(request, "users/2fa_settings.html", context)

        # TOTP code verification
        elif action == "verify_totp":
            code = request.POST.get("totp_code")
            if verify_totp(user.twofa_totp_secret, code):
                user.totp_enabled = True
                user.save()
                log_user_action_json(
                    user=user,
                    action="enable_totp",
                    request=request,
                )
                messages.success(request, "2FA TOTP activated.")
                return redirect("twofa_settings")
            else:
                messages.error(request, "Invalid TOTP code.")

                uri = get_totp_uri(user, user.twofa_totp_secret)
                qr_base64 = generate_qr_code_base64(uri)

                context.update(
                    {
                        "qr_code_url": qr_base64,
                        "totp_secret": user.twofa_totp_secret,
                        "totp_uri": uri,
                        "step": "verify_totp",
                    }
                )
                return render(request, "users/2fa_settings.html", context)

        # TOTP deactivation
        elif action == "disable_totp":
            password = request.POST.get("password")
            code = request.POST.get("totp_code")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
            elif not verify_totp(user.twofa_totp_secret, code):
                messages.error(request, "Code TOTP invalide.")
            else:
                user.totp_enabled = False
                user.twofa_totp_secret = ""
                user.save()
                log_user_action_json(
                    user=user,
                    action="disable_totp",
                    request=request,
                )
                messages.success(request, "2FA TOTP désactivée.")
                return redirect("twofa_settings")
            return redirect("twofa_settings")

        # Revoking a trusted device
        elif action == "revoke_device":
            device_id = request.POST.get("revoke_device_id")
            device = get_object_or_404(TrustedDevice, id=device_id, user=user)
            device.delete()
            messages.success(request, "Appareil révoqué avec succès.")
            return redirect("twofa_settings")

    return render(request, "users/2fa_settings.html", context)


# ========= VIEWS UPDATED =========


def login_view(request):
    """Vue de connexion avec 2FA améliorée"""
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_location_from_ip(ip)

    step = request.POST.get("step", "login")
    context = {"step": step}
    user = None

    if step == "login":
        form = LoginForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            identifier = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember_device = form.cleaned_data.get("remember_device")
            request.session["remember_device"] = remember_device
            # Rechercher l'utilisateur par email ou username
            user_qs = CustomUser.objects.filter(
                email=identifier
            ) | CustomUser.objects.filter(username=identifier)

            if not user_qs.exists():
                messages.error(
                    request,
                    mark_safe(
                        f"Aucun compte trouvé. <a href='{reverse('register')}' class='alert-link'>Créer un compte</a>."
                    ),
                )
                return render(request, "users/login.html", {"form": form, "step": step})

            user = authenticate(request, username=identifier, password=password)
            if user is None:
                messages.error(
                    request, "Email/nom d'utilisateur ou mot de passe incorrect"
                )
                return render(request, "users/login.html", {"form": form, "step": step})

            if not user.is_email_verified:
                messages.warning(
                    request,
                    mark_safe(
                        f"Vérifiez votre email avant de vous connecter. <a href='{reverse('verify_email')}' class='alert-link'>Renvoyer le code</a>"
                    ),
                )
                request.session["verification_email"] = user.email
                return redirect("verify_email")

            # Gérer "Se souvenir de moi"
            if remember_device:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(
                    0
                )  # Session expirée à la fermeture du navigateur

            # Vérifier si c'est un appareil de confiance
            if (user.email_2fa_enabled or user.totp_enabled) and is_trusted_device(
                request, user
            ):
                request.session.pop("remember_device", False)
                return login_success(
                    request,
                    user,
                    ip,
                    user_agent,
                    location,
                    twofa_method="trusted_device",
                )

            # Lancer le processus 2FA si activé
            request.session["pre_2fa_user_id"] = user.id

            # Si les deux méthodes sont activées, laisser choisir
            if user.email_2fa_enabled and user.totp_enabled:
                return render(
                    request,
                    "users/login.html",
                    {
                        "form": Choose2FAMethodForm(),
                        "step": "choose_2fa",
                        "user": user,
                    },
                )

            # Si seul l'email 2FA est activé
            elif user.email_2fa_enabled:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()

                # AJOUTER: Initialiser les données de session
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

                success = send_2FA_email(user, code)
                if success:
                    return render(
                        request,
                        "users/login.html",
                        {
                            "form": Email2FAForm(),
                            "step": "email_2fa",
                            "user": user,
                            "can_resend": False,  # Nouveau code vient d'être envoyé
                        },
                    )
                else:
                    form.add_error("email", "Error sending 2FA email.")

            # Si seul le TOTP est activé
            elif user.totp_enabled:
                return render(
                    request,
                    "users/login.html",
                    {
                        "form": TOTP2FAForm(),
                        "step": "totp_2fa",
                        "user": user,
                    },
                )

            # Pas de 2FA activée
            print(f"login_view:{remember_device}")
            return login_success(
                request=request,
                user=user,
                ip=ip,
                user_agent=user_agent,
                location=location,
                twofa_method=None,
                remember_device=remember_device,
            )

        return render(request, "users/login.html", {"form": form, "step": step})

    elif step == "choose_2fa":
        form = Choose2FAMethodForm(request.POST or None)

        if request.method == "POST" and form.is_valid():
            user = CustomUser.objects.get(pk=request.session.get("pre_2fa_user_id"))
            if not user:
                messages.error(request, "Session expirée.")
                return redirect("login")

            method = form.cleaned_data["twofa_method"]

            if method == "email" and user.email_2fa_enabled:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()

                # AJOUTER: Initialiser les données de session
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

                send_2FA_email(user, code)
                return render(
                    request,
                    "users/login.html",
                    {
                        "form": Email2FAForm(),
                        "step": "email_2fa",
                        "user": user,
                        "can_resend": False,  # Nouveau code vient d'être envoyé
                    },
                )

            elif method == "totp" and user.totp_enabled:
                return render(
                    request,
                    "users/login.html",
                    {
                        "form": TOTP2FAForm(),
                        "step": "totp_2fa",
                        "user": user,
                    },
                )

        return render(
            request,
            "users/login.html",
            {"form": form, "step": step, "user": get_user_from_session(request)},
        )

    elif step in ["email_2fa", "totp_2fa"]:
        FormClass = Email2FAForm if step == "email_2fa" else TOTP2FAForm
        form = FormClass(request.POST or None)

        user = get_user_from_session(request)
        if not user:
            messages.error(request, "Session expirée.")
            return redirect("login")

        # Gestion du renvoi de code email - CORRIGÉ
        if (
            request.method == "POST"
            and request.POST.get("resend_code")
            and step == "email_2fa"
        ):
            # Utiliser les données de session ET l'utilisateur pour vérifier le délai
            session_data = request.session.get("login_data", {})

            # Vérifier avec les données de session ET l'utilisateur
            can_resend_session = can_resend_code(session_data)
            can_resend_user = (
                user.can_send_verification_code()
                if hasattr(user, "can_send_verification_code")
                else True
            )

            if can_resend_session and can_resend_user:
                # Générer un nouveau code
                new_code = generate_email_code()

                # Mettre à jour l'utilisateur
                user.email_2fa_code = new_code
                user.email_2fa_sent_at = timezone.now()
                user.save()

                # Mettre à jour les données de session
                session_data.update(
                    {
                        "verification_code": new_code,
                        "code_sent_at": timezone.now().isoformat(),
                        "code_attempts": 0,
                    }
                )
                request.session["login_data"] = session_data

                # Envoyer l'email
                success = send_2FA_email(user, new_code)

                if success:
                    messages.success(request, "Nouveau code envoyé à votre email.")
                else:
                    messages.error(request, "Erreur lors de l'envoi du code.")
            else:
                messages.warning(
                    request, "Attendez 2 minutes avant de demander un nouveau code."
                )

            # IMPORTANT: Retourner la vue avec can_resend calculé
            session_data = request.session.get("login_data", {})
            can_resend = can_resend_code(session_data)

            return render(
                request,
                "users/login.html",
                {"form": form, "step": step, "user": user, "can_resend": can_resend},
            )

        # Validation du code soumis
        if request.method == "POST" and form.is_valid():
            twofa_code = form.cleaned_data["twofa_code"]
            remember_device = request.session.get("remember_device", False)

            # Validation du code
            valid = (
                is_email_code_valid(user, twofa_code)
                if step == "email_2fa"
                else verify_totp(user.twofa_totp_secret, twofa_code)
            )

            if valid:
                # Nettoyer le code email et les données de session après utilisation
                if step == "email_2fa":
                    user.email_2fa_code = None
                    user.email_2fa_sent_at = None
                    user.save()
                    # Nettoyer les données de session
                    request.session.pop("login_data", None)

                return login_success(
                    request,
                    user,
                    ip,
                    user_agent,
                    location,
                    twofa_method=step,
                    remember_device=remember_device,
                )
            else:
                messages.error(request, "Code invalide ou expiré.")

        # IMPORTANT: Préparer les données pour le template avec can_resend calculé
        session_data = request.session.get("login_data", {})
        can_resend = can_resend_code(session_data)

        return render(
            request,
            "users/login.html",
            {
                "form": form,
                "step": step,
                "user": user,
                "can_resend": can_resend,  # S'assurer que cette variable est toujours passée
            },
        )


@csrf_exempt
@require_POST
def resend_2fa_code_view(request):
    """Vue AJAX pour renvoyer le code 2FA par email"""
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
