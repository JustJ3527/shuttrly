# === Django Imports ===
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordResetForm as DjangoPasswordResetForm,
    SetPasswordForm as DjangoSetPasswordForm,
)
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# === Project Models ===
from .models import CustomUser
from .validators import UsernameValidator
from .validators import CustomPasswordValidator


# ===============================================
# REGISTER FORMS
# ===============================================
class RegisterStep1Form(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
                "type": "email",
            }
        ),
    )


class RegisterStep2Form(forms.Form):
    first_name = forms.CharField(
        label="First name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your first name"}
        ),
    )
    last_name = forms.CharField(
        label="Last name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your last name"}
        ),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "placeholder": "YYYY-MM-DD",
                "type": "date",
            }
        ),
    )


class RegisterStep3Form(forms.Form):
    bio = forms.CharField(
        label="Biography",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Tell us a bit about yourself...",
                "rows": 4,
            }
        ),
        required=False,
    )
    is_private = forms.BooleanField(
        label="Private account",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "isPrivateCheckbox"}
        ),
        required=False,
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        required=False,
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter a password",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
                "autocomplete": "new-password-confirm",
            }
        ),
    )


# ===============================================
# LOGIN FORMS
# ===============================================
class LoginForm(forms.Form):
    email = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "your@email.com ou username",
                "autocomplete": "username",
                "id": "id_email",
            }
        ),
        help_text="You can use your email address or username to log in.",
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your password",
                "autocomplete": "current-password",
                "id": "id_password",
            }
        ),
    )
    remember_device = forms.BooleanField(
        required=False,
        label="Remember this device",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input", "id": "id_remember_device"}
        ),
    )


class Choose2FAMethodForm(forms.Form):
    TWOFA_CHOICES = [
        ("email", "Code by email"),
        ("totp", "Authentification app (TOTP)"),
    ]

    twofa_method = forms.ChoiceField(
        label="Méthode de vérification",
        choices=TWOFA_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        help_text="Choose your 2FA method",
    )


class Email2FAForm(forms.Form):
    twofa_code = forms.CharField(
        label="Code de vérification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "maxlength": "6",
                "pattern": "[0-9]{6}",
                "autocomplete": "one-time-code",
                "id": "id_twofa_code",
            }
        ),
        help_text="Enter the 6-digit code sent to your email address",
    )


class TOTP2FAForm(forms.Form):
    twofa_code = forms.CharField(
        label="Code d'authentification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "maxlength": "6",
                "pattern": "[0-9]{6}",
                "autocomplete": "one-time-code",
                "id": "id_twofa_code",
            }
        ),
        help_text="Code from your authentication app (Google Authenticator, Authy, etc.)",
    )


# ===============================================
# EDIT PROFILE FORMS
# ===============================================
class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "date_of_birth",
            "bio",
            "is_private",
            "profile_picture",
        ]
        labels = {
            "email": "Email address",
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "date_of_birth": "Date of birth",
            "bio": "Biography",
            "is_private": "Private account",
            "profile_picture": "Profile picture",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                    "type": "email",
                }
            ),
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Choose a username"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your first name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your last name"}
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "YYYY-MM-DD",
                    "type": "date",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us a bit about yourself...",
                    "rows": 4,
                }
            ),
            "is_private": forms.CheckboxInput(
                attrs={"class": "form-check-input", "id": "isPrivateCheckbox"}
            ),
            "profile_picture": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add username validator to the username field
        self.fields["username"].validators.append(UsernameValidator())
        self.fields["username"].help_text = (
            "3-30 characters, letters/numbers/underscores only. Cannot start with numbers/underscores or end with underscores."
        )


# class LoginForm(forms.Form):
#     email = forms.CharField(
#         label="Email or username",
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#                 "placeholder": "Enter your email or username",
#             }
#         ),
#     )
#     password = forms.CharField(
#         label="Password",
#         widget=forms.PasswordInput(
#             attrs={
#                 "class": "form-control",
#                 "placeholder": "Enter your password",
#             }
#         ),
#     )


class RegisterStep2Form(forms.Form):
    verification_code = forms.CharField(
        label="Verification code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "maxlength": "6",
                "pattern": "[0-9]{6}",
                "autocomplete": "one-time-code",
            }
        ),
        help_text="Enter the 6-digit code received by email",
    )


class RegisterStep3Form(forms.Form):
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your first name",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your last name",
                "autocomplete": "family-name",
            }
        ),
    )
    date_of_birth = forms.DateField(
        label="Date de naissance",
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date", "autocomplete": "bday"}
        ),
        help_text="You must be at least 16 years old",
    )


class RegisterStep4Form(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "username",
                "autocomplete": "username",
                "id": "username-input",
            }
        ),
        validators=[UsernameValidator()],
        help_text="3-30 characters, letters/numbers/underscores only. Cannot start with numbers/underscores or end with underscores.",
    )


class RegisterStep5Form(forms.Form):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your password",
                "autocomplete": "new-password",
                "id": "password1",
            }
        ),
        help_text="At least 12 characters, with uppercase, lowercase, digits, and special characters",
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
                "autocomplete": "new-password",
                "id": "password2",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The passwords do not match.")

            # Validate password strength using our custom validator

            validator = CustomPasswordValidator()
            try:
                validator.validate(password1)
            except ValidationError as e:
                self.add_error("password1", str(e))

        return cleaned_data


# ===============================================
# PROFILE EDITING FORMS
# ===============================================
class EditProfileStep1Form(forms.Form):
    """Step 1: Email verification for profile editing"""

    email = forms.EmailField(
        label="New email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your new email address",
                "type": "email",
                "autocomplete": "email",
            }
        ),
        help_text="We'll send a verification code to this new email address",
    )


class EditProfileStep2Form(forms.Form):
    """Step 2: Email verification code"""

    verification_code = forms.CharField(
        label="Verification code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control verification-code-input",
                "placeholder": "000000",
                "maxlength": "6",
                "pattern": "[0-9]{6}",
                "autocomplete": "one-time-code",
            }
        ),
        help_text="Enter the 6-digit code received by email",
    )


class EditProfileStep3Form(forms.Form):
    """Step 3: Personal information"""

    first_name = forms.CharField(
        label="First name",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your first name",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your last name",
                "autocomplete": "family-name",
            }
        ),
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "autocomplete": "bday",
            }
        ),
        help_text="You must be at least 16 years old",
    )
    bio = forms.CharField(
        label="Biography",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Tell us a bit about yourself...",
                "rows": 4,
            }
        ),
    )
    is_private = forms.BooleanField(
        label="Private account",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    profile_picture = forms.ImageField(
        label="Profile picture",
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )


class EditProfileStep4Form(forms.Form):
    """Step 4: Username change"""

    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a new username",
                "autocomplete": "username",
                "id": "username-input",
            }
        ),
        validators=[UsernameValidator()],
        help_text="3-30 characters, letters/numbers/underscores only. Cannot start with numbers/underscores or end with underscores.",
    )


class EditProfileStep5Form(forms.Form):
    """Step 5: Password change"""

    current_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password",
                "autocomplete": "current-password",
            }
        ),
        help_text="Enter your current password to confirm changes",
    )
    password1 = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-field",
                "placeholder": "Enter new password (optional)",
                "autocomplete": "new-password",
                "id": "password1",
            }
        ),
        help_text="Leave blank if you don't want to change your password. At least 12 characters, with uppercase, lowercase, digits, and special characters",
    )
    password2 = forms.CharField(
        label="Confirm new password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-field",
                "placeholder": "Confirm new password",
                "autocomplete": "new-password",
                "id": "password2",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if not password1:
                raise forms.ValidationError("Please enter a new password.")
            if not password2:
                raise forms.ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise forms.ValidationError("The passwords do not match.")

            # Validate password strength using our custom validator
            validator = CustomPasswordValidator()
            try:
                validator.validate(password1)
            except ValidationError as e:
                self.add_error("password1", str(e))

        return cleaned_data


# ===============================================
# SIMPLE PROFILE EDITING FORM
# ===============================================


class SimpleProfileEditForm(forms.ModelForm):
    """Simple form for editing profile information in one page."""

    current_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password to change password",
            }
        ),
        help_text="Required only if you want to change your password",
    )

    password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password (optional)",
            }
        ),
        help_text="Leave blank if you don't want to change your password",
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm new password",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "date_of_birth",
            "bio",
            "is_private",
            "profile_picture",
        ]
        labels = {
            "email": "Email address",
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "date_of_birth": "Date of birth",
            "bio": "Biography",
            "is_private": "Private account",
            "profile_picture": "Profile picture",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                    "type": "email",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Choose a username",
                    "id": "username-input",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your first name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your last name",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us a bit about yourself...",
                    "rows": 3,
                }
            ),
            "is_private": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "profile_picture": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add username validator
        self.fields["username"].validators.append(UsernameValidator())
        self.fields["username"].help_text = (
            "3-30 characters, letters/numbers/underscores only. Cannot start with numbers/underscores or end with underscores."
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        current_password = cleaned_data.get("current_password")

        # If any password field is filled, all must be filled
        if password1 or password2 or current_password:
            if not current_password:
                raise forms.ValidationError(
                    "Current password is required to change your password."
                )
            if not password1:
                raise forms.ValidationError("New password is required.")
            if not password2:
                raise forms.ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise forms.ValidationError("The new passwords do not match.")

            # Validate password strength
            if password1:
                validator = CustomPasswordValidator()
                try:
                    validator.validate(password1)
                except ValidationError as e:
                    self.add_error("password1", str(e))

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and hasattr(self, "instance") and self.instance:
            # Check if email is already used by another user
            if (
                CustomUser.objects.filter(email=email)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError(
                    "An account with this email already exists."
                )
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and hasattr(self, "instance") and self.instance:
            # Check if username is already used by another user
            if (
                CustomUser.objects.filter(username=username)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError("This username is already taken.")
        return username


# ===============================================
# SEPARATED PROFILE FORMS
# ===============================================


class PersonalSettingsForm(forms.ModelForm):
    """Form for personal/private settings (email, password, date of birth, privacy, 2FA)."""

    current_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password to change password",
            }
        ),
        help_text="Required only if you want to change your password",
    )

    password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password (optional)",
            }
        ),
        help_text="Leave blank if you don't want to change your password",
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm new password",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = ["email", "date_of_birth", "is_private"]
        labels = {
            "email": "Email address",
            "date_of_birth": "Date of birth",
            "is_private": "Private account",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                    "type": "email",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "is_private": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        current_password = cleaned_data.get("current_password")

        # If any password field is filled, all must be filled
        if password1 or password2 or current_password:
            if not current_password:
                raise forms.ValidationError(
                    "Current password is required to change your password."
                )
            if not password1:
                raise forms.ValidationError("New password is required.")
            if not password2:
                raise forms.ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise forms.ValidationError("The new passwords do not match.")

            # Validate password strength
            if password1:
                validator = CustomPasswordValidator()
                try:
                    validator.validate(password1)
                except ValidationError as e:
                    self.add_error("password1", str(e))

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and hasattr(self, "instance") and self.instance:
            # Check if email is already used by another user
            if (
                CustomUser.objects.filter(email=email)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError(
                    "An account with this email already exists."
                )
        return email


class PublicProfileForm(forms.ModelForm):
    """Form for public profile information (name, username, bio, profile picture)."""

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "bio", "profile_picture"]
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "username": "Username",
            "bio": "Biography",
            "profile_picture": "Profile picture",
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your first name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your last name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Choose a username",
                    "id": "username-input",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us a bit about yourself...",
                    "rows": 4,
                }
            ),
            "profile_picture": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add username validator
        self.fields["username"].validators.append(UsernameValidator())
        self.fields["username"].help_text = (
            "3-30 characters, letters/numbers/underscores only. Cannot start with numbers/underscores or end with underscores."
        )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and hasattr(self, "instance") and self.instance:
            # Check if username is already used by another user
            if (
                CustomUser.objects.filter(username=username)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError("This username is already taken.")
        return username


# =============================================================================
# CUSTOM PASSWORD RESET FORMS
# =============================================================================


class CustomPasswordResetForm(DjangoPasswordResetForm):
    """
    Custom password reset form that uses our email field.
    """

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not CustomUser.objects.filter(email=email).exists():
            # Don't reveal if email exists or not (security)
            pass
        return email


class CustomSetPasswordForm(DjangoSetPasswordForm):
    """
    Custom set password form that validates password strength and ensures
    the new password is different from the old one.
    """

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        # Store the user for validation
        self.user = user

    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")

        if password1:
            # Check if new password is different from old password
            if self.user.check_password(password1):
                raise forms.ValidationError(
                    "Your new password must be different from your current password."
                )

            # Validate password strength using our custom validator
            validator = CustomPasswordValidator()
            try:
                validator.validate(password1)
            except ValidationError as e:
                raise forms.ValidationError(str(e))

        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")

        return cleaned_data


# =============================================================================
# SETTINGS DASHBOARD FORMS
# =============================================================================


class GeneralSettingsForm(forms.ModelForm):
    """Form for general user information (email, password, date of birth)."""

    current_password = forms.CharField(
        label="Current Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password to change password",
            }
        ),
        help_text="Required only if you want to change your password",
    )

    password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password (optional)",
            }
        ),
        help_text="Leave blank if you don't want to change your password",
    )

    password2 = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm new password",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = ["email", "date_of_birth"]
        labels = {
            "email": "Email Address",
            "date_of_birth": "Date of Birth",
        }
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                    "type": "email",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        current_password = cleaned_data.get("current_password")

        # If any password field is filled, all must be filled
        if password1 or password2 or current_password:
            if not current_password:
                raise forms.ValidationError(
                    "Current password is required to change your password."
                )
            if not password1:
                raise forms.ValidationError("New password is required.")
            if not password2:
                raise forms.ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise forms.ValidationError("The new passwords do not match.")

            # Validate password strength
            if password1:
                validator = CustomPasswordValidator()
                try:
                    validator.validate(password1)
                except ValidationError as e:
                    self.add_error("password1", str(e))

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and hasattr(self, "instance") and self.instance:
            # Check if email is already used by another user
            if (
                CustomUser.objects.filter(email=email)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError(
                    "An account with this email already exists."
                )
        return email


class PrivacySettingsForm(forms.ModelForm):
    """Form for privacy and security settings (2FA, private account, etc.)."""

    class Meta:
        model = CustomUser
        fields = ["is_private"]
        labels = {
            "is_private": "Private Account",
        }
        widgets = {
            "is_private": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "hx-post": "",  # Will be set dynamically
                    "hx-swap": "none",
                }
            ),
        }


class MediaSettingsForm(forms.ModelForm):
    """Form for media and profile picture management."""

    class Meta:
        model = CustomUser
        fields = ["profile_picture"]
        labels = {
            "profile_picture": "Profile Picture",
        }
        widgets = {
            "profile_picture": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
        }


class PreferencesSettingsForm(forms.Form):
    """Form for user preferences (notifications, language, timezone)."""

    # Placeholder form for future preferences
    # This can be expanded later with actual preference fields
    notifications_enabled = forms.BooleanField(
        label="Enable Notifications",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "hx-post": "",  # Will be set dynamically
                "hx-swap": "none",
            }
        ),
    )

    language = forms.ChoiceField(
        label="Language",
        choices=[
            ("en", "English"),
            ("fr", "Français"),
        ],
        initial="en",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    timezone = forms.ChoiceField(
        label="Timezone",
        choices=[
            ("UTC", "UTC"),
            ("Europe/Paris", "Europe/Paris"),
            ("America/New_York", "America/New_York"),
        ],
        initial="UTC",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class AdvancedSecurityForm(forms.Form):
    """Form for advanced security settings (sessions, login history)."""

    # This form will be used to display security information
    # and manage active sessions
    pass


# =============================================================================
# EXISTING FORMS
# =============================================================================
