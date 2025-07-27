from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm

# Create your views here.
def register_view(request):
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

class CustomLoginView(LoginView):
    template_name = 'users/login.html'  # Specify your custom login template
