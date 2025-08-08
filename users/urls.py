from django.contrib import admin
from django.urls import path, include
from .views import *
from . import views

urlpatterns = [
    # Registration in 6 steps
    path(
        "register/",
        register_view,
        name="register",
    ),
    path(
        "check-username/",
        check_username_availability,
        name="check_username_availability",
    ),
    path(
        "resend-code/",
        resend_verification_code_view,
        name="resend_verification_code",
    ),
    # Login in 3 steps with 2FA
    path(
        "login/",
        login_view,
        name="login",
    ),
    path(
        "resend-2fa-code/",
        resend_email_2fa_code,
        name="resend_email_2fa_code",
    ),
    path(
        "profile/",
        profile_view,
        name="profile",
    ), 
    path(
        "logout/",
        logout_view,
        name="logout",
    ),
    path(
        "resend-verification-code/",
        resend_verification_code_view,
        name="resend_verification_code_view",
    ),
    path(
        "account/delete/",
        delete_account_view,
        name="delete_account",
    ),
    path(
        "2fa/",
        twofa_settings_view,
        name="twofa_settings",
    ),
]
