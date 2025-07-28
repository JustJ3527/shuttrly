from django.urls import path
from .views import register_view, login_view, profile_view, logout_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),  # Custom login view
    path('profile/', profile_view, name='profile'),  # Profile view for logged-in users
    path('logout/', logout_view, name='logout'),
]