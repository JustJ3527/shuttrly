from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

# Create your models here.

# Custom manager to handle user creation (standard  user + superuser)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_field):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(email=emaail, username=username, **extra_field)
        user.set_password(password) # Hash the password
        user.save()
        return user
    
    def create_superuser(self, email, username, password=None, **extra_field):
        # Ensure superuser has staff and supooeruser privileges
        extra_field.setdefault('is_staff', True)
        extra_field.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_field)
    
# Custom user model
classCustomUser()