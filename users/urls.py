from django.contrib import admin
from django.urls import path, include
from .views import *
from . import views

urlpatterns = [
    path(
        "register/",
        register_view,
        name="register",
    ),
    path(
        "login/",
        login_view,
        name="login",
    ),  # Custom login view
    path(
        "profile/",
        profile_view,
        name="profile",
    ),  # Profile view for logged-in users
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
]
