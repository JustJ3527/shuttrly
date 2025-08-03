from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),  # Custom login view
    path('profile/', profile_view, name='profile'),  # Profile view for logged-in users
    path('logout/', logout_view, name='logout'),

    path('verify-email/', verify_email_view, name='verify_email'),
    path('resend-verification-code/', resend_verification_code_view, name='resend_verification_code_view'),
    path('account/delete/', delete_account_view, name='delete_account'),
    path('2fa/', twofa_settings_view, name='twofa_settings')
]