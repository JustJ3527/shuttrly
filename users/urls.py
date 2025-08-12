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
        "resend-verfication-code/",
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
        resend_2fa_code_view,
        name="resend_2fa_code_view",
    ),
    path(
        "profile/",
        profile_view,
        name="profile",
    ),
    # Profile editing - separated approach
    path(
        "profile/personal-settings/",
        personal_settings_view,
        name="personal_settings",
    ),
    path(
        "profile/public-profile/",
        public_profile_view,
        name="public_profile",
    ),
    # Profile editing - simple approach
    path(
        "profile/edit-simple/",
        edit_profile_simple_view,
        name="edit_profile_simple",
    ),
    # Profile editing in 5 steps (legacy)
    path(
        "profile/edit/",
        edit_profile_view,
        name="edit_profile",
    ),
    path(
        "profile/resend-verification-code/",
        resend_profile_verification_code_view,
        name="resend_profile_verification_code",
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
