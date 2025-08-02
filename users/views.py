# Context: Django user management views with detailed JSON logging.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth import logout, authenticate, login
from .models import CustomUser
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.safestring import mark_safe
from logs.utils import log_user_action_json  # JSON logging utility
from .utils import schedule_profile_picture_deletion
from django.conf import settings


# Decorators

def redirect_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def redirect_not_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# Helper to get IP and User-Agent from request

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', 'unknown')


# Views

@redirect_authenticated_user
def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            ip = get_client_ip(request)
            user.ip_address = ip
            user.save()

            user_agent = get_user_agent(request)
            log_user_action_json(
                user=user,
                action='register',
                request=request,
                extra_info=f"IP: {ip} | User-Agent: {user_agent}"
            )

            success, msg = user.send_verification_email()
            if success:
                messages.success(request, "Account created successfully. A code has been sent.")
                request.session['verification_email'] = user.email
                return redirect('verify_email')
            else:
                messages.error(request, f"Account created but error sending code: {msg}")
                request.session['verification_email'] = user.email
                return redirect('verify_email')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


@redirect_authenticated_user
def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('email')
        password = request.POST.get('password')

        # Check user existence by email or username
        if not (CustomUser.objects.filter(email=identifier).exists() or CustomUser.objects.filter(username=identifier).exists()):
            messages.error(request, mark_safe(
                f"No account found with this email. <a href='{reverse('register')}'>Create an account</a>."
            ))
            return render(request, 'users/login.html')

        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            if not user.is_email_verified:
                messages.warning(request, 'You must verify your email before login.')
                request.session['verification_email'] = user.email
                return redirect('verify_email')

            login(request, user)
            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()

            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            log_user_action_json(
                user=user,
                action='login',
                request=request,
                extra_info=f"IP: {ip} | User-Agent: {user_agent}"
            )

            messages.success(request, f"Welcome {user.first_name or user.username}")
            return redirect('profile')
        else:
            messages.error(request, 'Email or password is incorrect')
            return render(request, 'users/login.html', {'error': 'Invalid email or password'})

    return render(request, 'users/login.html')


def verify_email_view(request):
    email = request.session.get('verification_email')
    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    if user.is_email_verified:
        messages.info(request, "Email already verified. You can login.")
        return redirect('login')

    if request.method == 'POST':
        submitted_code = request.POST.get('verification_code', '').strip()
        if not submitted_code:
            messages.error(request, "Please enter the verification code.")
            return render(request, 'users/verify_email.html', {'email': email})

        if user.verify_email(submitted_code):
            if 'verification_email' in request.session:
                del request.session['verification_email']

            user.backend = 'users.backend.SuperuserUsernameBackend'
            login(request, user)

            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()

            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            log_user_action_json(
                user=user,
                action='verify_email',
                request=request,
                extra_info=f"Verification code used: {submitted_code} | IP: {ip} | User-Agent: {user_agent}"
            )

            messages.success(request, f"Email verified successfully! Welcome {user.first_name}")
            return redirect('profile')

        else:
            messages.error(request, "The code is incorrect or has expired.")

    can_resend = user.can_send_verification_code()
    time_until_resend = 0
    if not can_resend and user.verification_code_sent_at:
        elapsed = timezone.now() - user.verification_code_sent_at
        time_until_resend = max(0, 15 - int(elapsed.total_seconds()))

    context = {
        'email': email,
        'can_resend': can_resend,
        'time_until_resend': time_until_resend,
    }
    return render(request, 'users/verify_email.html', context)


def resend_verification_code(request):
    if request.method != 'POST':
        return redirect('verify_email')

    email = request.session.get('verification_email')
    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    if not user.can_send_verification_code():
        messages.warning(request, "You must wait 2 minutes before requesting a new code.")
        return redirect('verify_email')

    success, msg = user.send_verification_email()
    if success:
        log_user_action_json(user=user, action='resend_code', request=request, extra_info='Verification code resent')
        messages.success(request, "A new code has been sent.")
    else:
        messages.error(request, msg)

    return redirect('verify_email')


from .utils import get_changes_dict
from .models import CustomUser
from .utils import get_client_ip, get_user_agent
# autres imports ...

@redirect_not_authenticated_user
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_data = CustomUser.objects.get(pk=user.pk)
            
            # Sauvegarder l'ancienne photo pour suppression différée
            old_profile_picture = None
            if 'profile_picture' in form.changed_data and old_data.profile_picture:
                old_profile_picture = old_data.profile_picture.name
            
            updated_user = form.save()

            # Supprimer l'ancienne photo plus tard
            if old_profile_picture:
                delay = getattr(settings, 'PROFILE_PICTURE_DELETION_DELAY_SECONDS', 86400)
                schedule_profile_picture_deletion(old_profile_picture, seconds=delay)

            ip = get_client_ip(request)
            user_agent = get_user_agent(request)

            # Utilise la fonction utilitaire ici
            changes_dict = get_changes_dict(old_data, updated_user, form.changed_data)

            extra_info = {
                "ip_address": ip,
                "user_agent": user_agent,
                "changes": changes_dict,
                "impacted_user_id": user.id,
            }

            log_user_action_json(user=user, action='update_profile', request=request, extra_info=extra_info)
            return redirect('profile')
        else:
            return render(request, 'users/profile.html', {'form': form})

    else:
        form = CustomUserUpdateForm(instance=user)
        return render(request, 'users/profile.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        user = request.user
        user.is_online = False
        user.save()

        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        log_user_action_json(user=user, action='logout', request=request, extra_info=f"IP: {ip} | User-Agent: {user_agent}")

    logout(request)
    return redirect('login')


@redirect_not_authenticated_user
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    user = request.user
    if user.is_superuser:
        messages.error(request, "A superuser can delete its account there.")
        return redirect('profile')

    if request.method == 'POST':
        action = request.POST.get('action')
        password = request.POST.get('password', '')

        if not user.check_password(password):
            messages.error(request, "Incorrect password.")
            return redirect('delete_account')

        ip = get_client_ip(request)
        user_agent = get_user_agent(request)

        if action == 'anonymize':
            user.anonymize()
            log_user_action_json(user=user, action='delete_account', request=request, extra_info=f"anonymized | IP: {ip} | User-Agent: {user_agent}")
            logout(request)
            messages.success(request, "Your account has been anonymized and deactivated.")
            return redirect('home')

        elif action == 'delete':
            with transaction.atomic():
                user_to_delete = user
                logout(request)
                log_user_action_json(user=user, action='delete_account', request=request, extra_info=f"deleted | IP: {ip} | User-Agent: {user_agent}")
                user_to_delete.delete()
            messages.success(request, "Votre compte a été supprimé définitivement.")
            return redirect('login')
        else:
            messages.error(request, "Invalid action.")
            return redirect('delete_account')

    # Display related object warnings
    related_warnings = []
    for rel in user._meta.get_fields():
        if (rel.one_to_many or rel.one_to_one) and rel.auto_created and not rel.concrete:
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
                    related_warnings.append({
                        "model": model_verbose,
                        "count": count,
                    })
            except Exception:
                pass

    return render(request, 'users/delete_account_confirm.html', {"related_warnings": related_warnings})