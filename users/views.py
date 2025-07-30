# Context: This code is part of a Django application for user management, including registration, login, profile editing, and logout functionalities.

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth import logout, authenticate, login
from .models import CustomUser
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods


# Redirect to profile if user is already authenticated
def redirect_authenticated_user(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

# Redirect to login if user is not authenticated
def redirect_not_authentifacted_user(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Register view for user registration
@redirect_authenticated_user
def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.ip_address = get_client_ip(request)
            user.save()

            # Send code by email after registration success
            success, msg = user.send_verification_email()
            if success:
                messages.success(request, "Account created successfully. A code has been sent.")

                # Stock email in user's session
                request.session['verification_email'] = user.email
                return redirect('verify_email')
            else:
                messages.error(request, f"Account created but there is an error with code : {msg}")
                request.session['verification_email'] = user.email
                return redirect('verify_email')
            
    else:
        form = CustomUserCreationForm()  # Reset form if invalid
    return render(request, 'users/register.html', {'form': form})

# Login view for user authentication
@redirect_authenticated_user
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            if not user.is_email_verified:
                messages.warning(request, 'You must verify your email before you can login.')
                request.session['verification_email'] = user.email
                return redirect('verify_email')
            

            login(request, user)
            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()
            messages.success(request, f"Welcome {user.first_name}")
            return redirect('profile')  # Redirect to profile page after login
        else:
            messages.error(request, 'email or password is incorrect')
            return render(request, 'users/login.html', {'error': 'Invalid email or password'})
        
    return render(request, 'users/login.html')


# Email verification
def verify_email_view(request):
    # Retrieve mail from session
    email = request.session.get('verification_email')
    if not email:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')
    
    # If user is already verified, redirect to login
    if user.is_email_verified:
        messages.info(request, "Your email is already verified. You can login.")
        return redirect('login')
    
    if request.method == 'POST':
        submitted_code = request.POST.get('verification_code', '').strip()

        if not submitted_code:
            messages.error(request, "Please enter code")
            return render(request, 'users/verify_email.html', {'email': email})
        
        # Check the code
        if user.verify_email(submitted_code):
            # Clean session
            if 'verification_email' in request.session:
                del request.session['verification_email']
            login(request, user)
            user.is_online = True
            user.last_login_date = timezone.now()
            user.save()
            messages.success(request, f"Email verified successfully! Welcome {user.first_name}")
            return redirect('profile')  # Redirect to profile page after login

        else:
            messages.error(request, "The code is incorrect or has expired.")

    # Calculate the time remaining before you can resend a code
    can_resend = user.can_send_verification_code()
    time_until_resend = 0

    if not can_resend and user.verification_code_sent_at:
        time_since_last = timezone.now() - user.verification_code_sent_at
        time_until_resend = max(0, 15 - int(time_since_last.total_seconds()))

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
        messages.error(request, "Session expired. Please register again")
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found")
        return redirect('register')
    
    # Check if user can receive a new code
    if not user.can_send_verification_code():
        messages.warning(request, "You must wait 2 minutes before you can ask a new code.")
        return redirect('verify_email')
    
    # Send a new code
    success, msg = user.send_verification_email()
    if success:
        messages.success(request, "A new code has been sent.")
    else:
        messages.error(request, msg)
    return redirect('verify_email')



# Profile view for editing user information
@redirect_not_authentifacted_user
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        else:
            # Si formulaire is not valid, we stay on that page with errors
            return render(request, 'users/profile.html', {'form': form})
    else:
        form = CustomUserUpdateForm(instance=user)
        return render(request, 'users/profile.html', {'form': form})
    
def logout_view(request):
    if request.user.is_authenticated:
        user = request.user
        user.is_online = False
        user.save()
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@redirect_not_authentifacted_user
@require_http_methods(["GET", "POST"])
def delete_account_view(request):
    user = request.user
    if user.is_superuser:
        messages.error(request, "A superuser can delete its account there.")
        return redirect('profile')

    if request.method == 'POST':
        action = request.POST.get('action') # 'delete' or 'anonymize'
        password = request.POST.get('password', '')
        
        # Validate password using Django's buit-in checker
        if not user.check_password(password):
            messages.error(request, "Incorrect password.")
            return redirect('delete_account')
       
        # Proceed based on selected action
        if action == 'anonymize':
            # Perform anonymization and then log the user out
            user.anonymize()
            logout(request)
            messages.success(request, "Your account has been anonymized and deactivated.")
            return redirect('home')
        
        elif action == 'delete':
            # Hard delete inside an atomic transaction to ensure integrity
            with transaction.atomic():
                # Keep a reference before logout to avoid losing the object
                user_to_delete = user
                logout(request)  # invalide la session
                user_to_delete.delete()
            messages.success(request, "Votre compte a été supprimé définitivement.")
            return redirect('login')
        else:
            messages.error(request, "Invalid action.")
            return redirect('delete_account')
        
    # GET: build a lightweight preview of related objects (count only)
    related_warnings = []
    # We introspect reverse relations to inform the what might be removed
    for rel in user._meta.get_fields():
        # We only care about reverse relations that Django created automatically
        if (rel.one_to_many or rel.one_to_one) and rel.auto_created and not rel.concrete:
            accessor = rel.get_accessor_name()
            try:
                if rel.one_to_many:
                    qs = getattr(user, accessor).all()
                    cnt = qs.count()
                else:
                    # one_to_one: presence is 0/1
                    obj = getattr(user, accessor, None)
                    cnt = 1 if obj else 0
                if cnt:
                    model_verbose = rel.related_model._meta.verbose_name_plural.title()
                    related_warnings.append({
                        "model": model_verbose,
                        "count": cnt,
                    })
            except Exception:
                # If a relation cannot be resolved, skip silently
                pass

    context = {
        "related_warnings": related_warnings,
    }    
    return render(request, 'users/delete_account_confirm.html', context)