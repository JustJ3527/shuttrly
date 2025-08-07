from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from users.models import CustomUser
import re
from django.core.exceptions import ValidationError


# ========= REGISTER FORMS =========
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
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Choose a username"}
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


# ========= LOGIN FORMS =========
class Choose2FAMethodForm(forms.Form):
    twofa_method = forms.ChoiceField(
        choices=[("email", "Code par e-mail"), ("totp", "App d’authentification")],
        widget=forms.RadioSelect,
        label="Choisissez votre méthode 2FA",
        initial="totp",
    )
    remember_device = forms.BooleanField(
        required=False, label="Faire confiance à cet appareil"
    )


class Email2FAForm(forms.Form):
    twofa_code = forms.CharField(
        label="Code received by email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter the 2FA code",
                "autofocus": "autofocus",
            }
        ),
    )
    remember_device = forms.BooleanField(
        required=False,
        label="Trust this device for 30 days",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )


class TOTP2FAForm(forms.Form):
    twofa_code = forms.CharField(
        label="TOTP code from your authenticator app",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "123 456 or 123456",
                "autocomplete": "one-time-code",
            }
        ),
    )
    remember_device = forms.BooleanField(
        required=False,
        label="Trust this device for 30 days",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )


# ========= EDIT PROFILE FORMS =========
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


class LoginForm(forms.Form):
    email = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email or username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
            }
        ),
    )


class RegisterStep1Form(forms.Form):
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "votre@email.com",
                "type": "email",
                "autocomplete": "email",
            }
        ),
    )


class RegisterStep2Form(forms.Form):
    verification_code = forms.CharField(
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
            }
        ),
        help_text="Entrez le code à 6 chiffres reçu par email",
    )


class RegisterStep3Form(forms.Form):
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Votre prénom",
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
                "placeholder": "Votre nom",
                "autocomplete": "family-name",
            }
        ),
    )
    date_of_birth = forms.DateField(
        label="Date de naissance",
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date", "autocomplete": "bday"}
        ),
        help_text="Vous devez avoir au moins 16 ans",
    )


class RegisterStep4Form(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "nom_utilisateur",
                "autocomplete": "username",
                "id": "username-input",
            }
        ),
        help_text="Seuls les lettres, chiffres et underscores sont autorisés",
    )


class RegisterStep5Form(forms.Form):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Votre mot de passe",
                "autocomplete": "new-password",
                "id": "password1",
            }
        ),
        help_text="Au moins 8 caractères",
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirmez votre mot de passe",
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
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data
