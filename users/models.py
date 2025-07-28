from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import os
import shutil
from django.conf import settings
from uuid import uuid4
from PIL import Image

# Create your models here.

def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_id = uuid4().hex
    filename = f"{unique_id}.{ext}"
    return os.path.join('profiles', unique_id, filename)

# Custom manager to handle user creation (standard  user + superuser)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_field):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_field)
        user.set_password(password) # Hash the password
        user.save()
        return user
    
    def create_superuser(self, email, username, password=None, **extra_field):
        # Ensure superuser has staff and supooeruser privileges
        extra_field.setdefault('is_staff', True)
        extra_field.setdefault('is_superuser', True)
        if extra_field.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_field.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, username, password, **extra_field)
    
# Custom user model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    def save(self, *args, **kwargs):
        try :
            old_user = CustomUser.objects.get(pk=self.pk)
            old_image_path = old_user.profile_picture.path if old_user.profile_picture else None
        except CustomUser.DoesNotExist:
            old_image_path = None
        
        super().save(*args, **kwargs) #Save the user first

    # If the photo has changed and is not the default one
        if old_image_path and self.profile_picture and old_image_path != self.profile_picture.path:
            if os.path.isfile(old_image_path) and 'profiles/default.jpg' not in old_image_path:
                os.remove(old_image_path) #Delete the old image file

                # Delete paret directory if empty
                old_folder = os.path.dirname(old_image_path)
                if os.path.isdir(old_folder) and not os.listdir(old_folder):
                    shutil.rmtree(old_folder)

        # Resize the image if it exists and is not the default one
        if self.profile_picture and self.profile_picture.name != 'profiles/default.jpg':
            img = Image.open(self.profile_picture.path)
            
            max_size = (300, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Extract lowercase extension
            ext = os.path.splitext(self.profile_picture.name)[1].lower()
            format_map = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.gif': 'GIF',
                '.bmp': 'BMP',
                '.tiff': 'TIFF',
                # add more formats if needed
            }
            img_format = format_map.get(ext, 'JPEG')  # Par défaut JPEG si inconnu
            img.save(self.profile_picture.path, format=img_format, optimize=True, quality=70)
            
    # Basic identidy fields
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    date_of_birth = models.DateField(blank=True, null=True)  # Optional field for the moment

    #Optional fields
    bio = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=user_directory_path, default='profiles/default.jpg')

    # IP tracking
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    # Permissions and status
    is_active = models.BooleanField(default=True) #Can the user log in?
    is_staff = models.BooleanField(default=False) #Can the user access the admin site?
    date_joined = models.DateTimeField(default=timezone.now) #When the user registered
    last_login_date = models.DateTimeField(blank=True, null=True) #Last login time
    is_online = models.BooleanField(default=False) #Online status
    
    # Link the custom manager
    objects = CustomUserManager()

    # Main authentication field
    USERNAME_FIELD = 'email' #Used to log in
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name',] 
    
    def __str__( self):
        return self.username #Used in admin and shell
