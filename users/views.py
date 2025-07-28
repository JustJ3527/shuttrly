# Context: This code is part of a Django application for user management, including registration, login, profile editing, and logout functionalities.

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login


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
            user.ip_adress = get_client_ip(request)
            user.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')  # Redirect to login page after successful registration
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
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('profile')  # Redirect to profile page after login
        else:
            messages.error(request, 'email or password is incorrect')
            return render(request, 'users/login.html', {'error': 'Invalid email or password'})
        
    return render(request, 'users/login.html')




# Profile view for editing user information
@redirect_not_authentifacted_user
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Assure-toi que 'profile' correspond bien à une URL nommée
        else:
            # Si le formulaire n'est pas valide, on reste sur la page avec les erreurs
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