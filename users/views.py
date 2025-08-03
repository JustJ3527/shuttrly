# Context: Django user management views with detailed JSON logging.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth import logout, authenticate, login
from .models import CustomUser, TrustedDevice
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.safestring import mark_safe
from logs.utils import log_user_action_json  # JSON logging utility
from django.conf import settings
from datetime import timedelta
from urllib.parse import urlencode
from django.contrib.auth import get_backends
from django.utils.formats import date_format
from .utils import (
    generate_email_code,
    send_email_code,
    is_email_code_valid,
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code_base64,
    verify_totp,
    schedule_profile_picture_deletion,
    is_trusted_device,
    create_trusted_device,
    get_location_from_ip,
    analyze_user_agent,
)

# Decorators


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


# Helper to get IP and User-Agent from request


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "unknown")


# Views


@redirect_authenticated_user
def register_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            ip = get_client_ip(request)
            user.ip_address = ip
            location = get_location_from_ip(ip)
            user.save()

            user_agent = get_user_agent(request)
            log_user_action_json(
                user=user,
                action="register",
                request=request,
                extra_info={
                    "ip_address": ip,
                    "user_agent": user_agent,
                    "impacted_user_id": user.id,
                    "location": location,
                },
            )

            success, msg = user.send_verification_email()
            if success:
                messages.success(
                    request, "Account created successfully. A code has been sent."
                )
                request.session["verification_email"] = user.email
                return redirect("verify_email")
            else:
                messages.error(
                    request, f"Account created but error sending code: {msg}"
                )
                request.session["verification_email"] = user.email
                return redirect("verify_email")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {"form": form})


@redirect_authenticated_user
def login_view(request):
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_location_from_ip(ip)
    step = "login"
    user = None
    context = {}

    if request.method == "POST":
        step = request.POST.get("step", "login")

        if step == "login":
            identifier = request.POST.get("email")
            password = request.POST.get("password")

            user_qs = CustomUser.objects.filter(
                email=identifier
            ) | CustomUser.objects.filter(username=identifier)
            if not user_qs.exists():
                messages.error(
                    request,
                    mark_safe(
                        f"No account found. <a href='{reverse('register')}'>Create one</a>."
                    ),
                )
                return render(request, "users/login.html")

            user = authenticate(request, username=identifier, password=password)
            if user is None:
                messages.error(request, "Email or password is incorrect")
                return render(request, "users/login.html")

            if not user.is_email_verified:
                messages.warning(request, "Verify your email before login.")
                request.session["verification_email"] = user.email
                return redirect("verify_email")

            # ==== Vérifie si appareil de confiance ====
            if (user.email_2fa_enabled or user.totp_enabled) and is_trusted_device(
                request, user
            ):
                user.backend = f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
                login(request, user)
                user.is_online = True
                user.last_login_date = timezone.now()
                user.save()

                log_user_action_json(
                    user,
                    "login",
                    request,
                    extra_info={
                        "2fa": "trusted_device",
                        "ip_address": ip,
                        "user_agent": user_agent,
                        "location": location,
                    },
                )

                response = redirect("profile")
                # mise à jour device
                create_trusted_device(response, user, request, ip, user_agent, location)
                return response

            # ==== Sinon : lancer 2FA ====
            request.session["pre_2fa_user_id"] = user.id

            if user.email_2fa_enabled and user.totp_enabled:
                context.update(
                    {"step": "choose_2fa", "user": user, "default_method": "totp"}
                )
                return render(request, "users/login.html", context)

            elif user.email_2fa_enabled:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()
                send_email_code(user, code)
                context.update({"step": "email_2fa", "user": user})
                return render(request, "users/login.html", context)

            elif user.totp_enabled:
                context.update({"step": "totp_2fa", "user": user})
                return render(request, "users/login.html", context)

            # Pas de 2FA activé
            user.backend = (
                f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
            )
            login(request, user)
            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()

            log_user_action_json(
                user,
                "login",
                request,
                extra_info={
                    "ip_address": ip,
                    "user_agent": user_agent,
                    "location": location,
                },
            )

            response = redirect("profile")
            return response

        elif step == "choose_2fa":
            method = request.POST.get("twofa_method")
            user = CustomUser.objects.get(pk=request.session.get("pre_2fa_user_id"))
            if not user:
                messages.error(request, "Session expired.")
                return redirect("login")

            remember_device = request.POST.get("remember_device") == "yes"
            request.session["remember_device"] = remember_device

            if method == "email" and user.email_2fa_enabled:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()
                send_email_code(user, code)
                context.update({"step": "email_2fa", "user": user})
                return render(request, "users/login.html", context)

            elif method == "totp" and user.totp_enabled:
                context.update({"step": "totp_2fa", "user": user})
                return render(request, "users/login.html", context)

            messages.error(request, "Invalid method.")
            return redirect("login")

        elif step in ["email_2fa", "totp_2fa"]:
            twofa_code = request.POST.get("twofa_code")
            user = CustomUser.objects.get(pk=request.session.get("pre_2fa_user_id"))

            if not user:
                messages.error(request, "Session expired.")
                return redirect("login")

            valid = (
                is_email_code_valid(user, twofa_code)
                if step == "email_2fa"
                else verify_totp(user.twofa_totp_secret, twofa_code)
            )

            if valid:
                user.backend = f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
                login(request, user)
                user.is_online = True
                user.last_login_date = timezone.now()
                user.save()

                response = redirect("profile")

                remember_device = request.session.get("remember_device", False)
                if remember_device:
                    # create trusted device...
                    create_trusted_device(
                        response, user, request, ip, user_agent, location
                    )

                log_user_action_json(
                    user,
                    "login",
                    request,
                    extra_info={
                        "2fa": "email" if step == "email_2fa" else "totp",
                        "ip_address": ip,
                        "user_agent": user_agent,
                        "location": location,
                    },
                )

                # Clean up session
                if "remember_device" in request.session:
                    del request.session["remember_device"]
                del request.session["pre_2fa_user_id"]

                return response

            else:
                messages.error(request, "Invalid or expired code.")
                context.update({"step": step, "user": user})
                return render(request, "users/login.html", context)

    return render(request, "users/login.html")


def verify_email_view(request):

    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_location_from_ip(ip)

    email = request.session.get("verification_email")
    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("register")

    if user.is_email_verified:
        messages.info(request, "Email already verified. You can login.")
        return redirect("login")

    if request.method == "POST":
        submitted_code = request.POST.get("verification_code", "").strip()
        if not submitted_code:
            messages.error(request, "Please enter the verification code.")
            return render(request, "users/verify_email.html", {"email": email})

        if user.verify_email(submitted_code):
            if "verification_email" in request.session:
                del request.session["verification_email"]

            user.backend = "users.backend.SuperuserUsernameBackend"
            user.backend = (
                f"{get_backends()[0].__module__}.{get_backends()[0].__class__.__name__}"
            )
            login(request, user)

            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()

            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            log_user_action_json(
                user=user,
                action="verify_email",
                request=request,
                extra_info={
                    "verification_code_used": submitted_code,
                    "user_Agent": user_agent,
                    "location": location,
                },
            )

            messages.success(
                request, f"Email verified successfully! Welcome {user.first_name}"
            )
            return redirect("profile")

        else:
            messages.error(request, "The code is incorrect or has expired.")

    can_resend = user.can_send_verification_code()
    time_until_resend = 0
    if not can_resend and user.verification_code_sent_at:
        elapsed = timezone.now() - user.verification_code_sent_at
        time_until_resend = max(0, 15 - int(elapsed.total_seconds()))

    context = {
        "email": email,
        "can_resend": can_resend,
        "time_until_resend": time_until_resend,
    }
    return render(request, "users/verify_email.html", context)


def resend_verification_code_view(request):
    if request.method != "POST":
        return redirect("verify_email")

    email = request.session.get("verification_email")
    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect("register")

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("register")

    if not user.can_send_verification_code():
        messages.warning(
            request, "You must wait 2 minutes before requesting a new code."
        )
        return redirect("verify_email")

    success, msg = user.send_verification_email()
    if success:
        log_user_action_json(
            user=user,
            action="resend_code",
            request=request,
            extra_info="Verification code resent",
        )
        messages.success(request, "A new code has been sent.")
    else:
        messages.error(request, msg)

    return redirect("verify_email")


from .utils import get_changes_dict
from .models import CustomUser
from .utils import get_client_ip, get_user_agent

# autres imports ...


@redirect_not_authenticated_user
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_data = CustomUser.objects.get(pk=user.pk)

            # Sauvegarder l'ancienne photo pour suppression différée
            old_profile_picture = None
            if "profile_picture" in form.changed_data and old_data.profile_picture:
                old_profile_picture = old_data.profile_picture.name

            updated_user = form.save()

            # Supprimer l'ancienne photo plus tard
            if old_profile_picture:
                delay = getattr(
                    settings, "PROFILE_PICTURE_DELETION_DELAY_SECONDS", 86400
                )
                schedule_profile_picture_deletion(old_profile_picture, seconds=delay)

            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            location = get_location_from_ip(ip)

            # Utilise la fonction utilitaire ici
            changes_dict = get_changes_dict(old_data, updated_user, form.changed_data)

            log_user_action_json(
                user=user,
                action="update_profile",
                request=request,
                extra_info={
                    "ip_address": ip,
                    "user_agent": user_agent,
                    "changes": changes_dict,
                    "impacted_user_id": user.id,
                    "location": location,
                },
            )
            return redirect("profile")
        else:
            return render(request, "users/profile.html", {"form": form})

    else:
        form = CustomUserUpdateForm(instance=user)
        return render(request, "users/profile.html", {"form": form})


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
                "ip_address": ip,
                "user_agent": user_agent,
                "impacted_user_id": user.id,
                "location": location,
            },
        )

    logout(request)
    return redirect("login")


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
                action="delete_account",
                request=request,
                extra_info=f"anonymized | IP: {ip} | User-Agent: {user_agent}",
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
                    extra_info=f"deleted | IP: {ip} | User-Agent: {user_agent}",
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


@redirect_not_authenticated_user
def twofa_settings_view(request):
    user = request.user
    trusted_devices = user.trusted_devices.all().order_by("-last_used_at")

    EMAIL_CODE_RESEND_DELAY_SECONDS = 120

    for device in trusted_devices:
        ua_info = analyze_user_agent(device.user_agent)
        device.device_type = ua_info["device_type"]
        device.device_family = ua_info["device_family"]
        device.browser_family = ua_info["browser_family"]
        device.browser_version = ua_info["browser_version"]
        device.os_family = ua_info["os_family"]
        device.os_version = ua_info["os_version"]
        device.is_current_device = device.device_token == request.COOKIES.get(
            "trusted_device"
        )

    context = {
        "trusted_devices": trusted_devices,
        # autres variables de contexte...
    }

    # Calcul du délai avant de pouvoir renvoyer un code email
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

        # === Annuler une opération en cours (ex : vérification code, configuration totp) ===
        if action == "cancel":
            # Supprime la session de code email et totp si en cours
            if step == "verify_email_code":
                user.email_2fa_code = ""
                user.email_2fa_sent_at = None
                user.save()
            elif step == "verify_totp":
                user.twofa_totp_secret = ""
                user.save()

            # Suppression éventuelle du cookie remember_device
            response = redirect(reverse("twofa_settings") + "?step=initial")
            response.delete_cookie("remember_device")
            return response

        # === Activation 2FA par email (envoi du code) ===
        elif action == "enable_email":
            password = request.POST.get("password")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
            else:
                code = generate_email_code()
                user.email_2fa_code = code
                user.email_2fa_sent_at = timezone.now()
                user.save()
                send_email_code(user, code)
                url = (
                    reverse("twofa_settings")
                    + "?"
                    + urlencode({"step": "verify_email_code"})
                )
                return redirect(url)

        # === Vérification du code email ===
        elif action == "verify_email_code":
            input_code = request.POST.get("email_code")
            if is_email_code_valid(user, input_code):
                user.email_2fa_enabled = True
                user.email_2fa_code = ""
                user.save()
                log_user_action_json(user, "enable_email_2fa", request)
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

        # === Désactivation 2FA par email ===
        elif action == "disable_email":
            password = request.POST.get("password")
            if not user.check_password(password):
                messages.error(request, "Mot de passe incorrect.")
                return redirect("twofa_settings")
            else:
                user.email_2fa_enabled = False
                user.email_2fa_code = ""
                user.save()
                log_user_action_json(user, "disable_email_2fa", request)
                messages.success(request, "Authentification par e-mail désactivée.")
                return redirect("twofa_settings")

        # === Renvoi du code email ===
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
                send_email_code(user, user.email_2fa_code)
                messages.success(request, "Nouveau code envoyé.")
            else:
                messages.error(
                    request, "Veuillez attendre avant de demander un nouveau code."
                )

            url = (
                reverse("twofa_settings")
                + "?"
                + urlencode({"step": "verify_email_code"})
            )
            return redirect(url)

        # === Activation TOTP (génération secret et QR code) ===
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

        # === Vérification du code TOTP ===
        elif action == "verify_totp":
            code = request.POST.get("totp_code")
            if verify_totp(user.twofa_totp_secret, code):
                user.totp_enabled = True
                user.save()
                log_user_action_json(user, "enable_totp", request)
                messages.success(request, "2FA TOTP activée.")
                return redirect("twofa_settings")
            else:
                messages.error(request, "Code TOTP invalide.")

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

        # === Désactivation TOTP ===
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
                log_user_action_json(user, "disable_totp", request)
                messages.success(request, "2FA TOTP désactivée.")
                return redirect("twofa_settings")
            return redirect("twofa_settings")

        # === Révocation d'un appareil de confiance ===
        elif action == "revoke_device":
            device_id = request.POST.get("revoke_device_id")
            device = get_object_or_404(TrustedDevice, id=device_id, user=user)
            device.delete()
            messages.success(request, "Appareil révoqué avec succès.")
            return redirect("twofa_settings")

    # En cas d'accès GET ou POST sans action reconnue
    return render(request, "users/2fa_settings.html", context)
