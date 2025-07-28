from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser

class CustomUserCreationForm(UserCreationForm):
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
            "profile_picture"
        ]


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Tous les champs modifiables par l'utilisateur
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'date_of_birth',
            'bio',
            'is_private',
            'profile_picture',
        ]