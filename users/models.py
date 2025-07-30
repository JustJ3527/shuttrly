from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import os
import shutil
from django.conf import settings
from uuid import uuid4
from PIL import Image
import random
import string
from django.core.mail import send_mail


# Create your models here.

def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_id = uuid4().hex
    filename = f"{unique_id}.{ext}"
    return os.path.join('profiles', unique_id, filename)

# Custom manager to handle user creation (standard  user + superuser)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        # Ensure explicit flags exist
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_email_verified', False)

        # Enforce names only for non-superusers
        if not extra_fields.get('is_superuser'):
            if not extra_fields.get('first_name'):
                raise ValueError("First name is required")
            if not extra_fields.get('last_name'):
                raise ValueError("Last name is required")
        
        email = self.normalize_email(email)

        # Ensure a sane default for regular users if the caller forgot to pass it
        extra_fields.setdefault('is_email_verified', False)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password) # Hash the password
        user.save()
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
            # For superuser, fill defaults if missing
        # Fill defaults for superuser
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        extra_fields['is_email_verified'] = True

        # If not provided, allow empty strings for names
        extra_fields.setdefault('first_name', '')
        extra_fields.setdefault('last_name', '')

        if not password:
            raise ValueError('Superuser must have a password.')

        return self.create_user(email, username, password, **extra_fields)
    
# Custom user model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    def save(self, *args, **kwargs):
        # Keep track of the previous profile picture path to clean it if changed
        try :
            old_user = CustomUser.objects.get(pk=self.pk)
            old_image_path = old_user.profile_picture.path if old_user.profile_picture else None
        except CustomUser.DoesNotExist:
            old_image_path = None
        
        super().save(*args, **kwargs) #Save the user first

    # If the photo  changed and is not the default iamge, delete the old file and its folder if empty
        if old_image_path and self.profile_picture and old_image_path != self.profile_picture.path:
            if os.path.isfile(old_image_path) and 'profiles/default.jpg' not in old_image_path:
                os.remove(old_image_path) #Delete the old image file

                # Delete paret directory if empty
                old_folder = os.path.dirname(old_image_path)
                if os.path.isdir(old_folder) and not os.listdir(old_folder):
                    shutil.rmtree(old_folder)

        # Resize the new image (if not default)
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
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
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
    
    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_sent_at = models.DateTimeField(blank=True, null=True)

    #G GDPR (=RGPD) / alternative to hard delete
    is_anonymized = models.BooleanField(default=False)

    # Link the custom manager
    objects = CustomUserManager()

    # Main authentication field
    USERNAME_FIELD = 'email' #Used to log in
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name'] 

    
    def __str__( self):
        return self.username #Used in admin and shell
    
    def _remove_profile_picture_file(self):
        try:
            if self.profile_picture and self.profile_picture.name and self.profile_picture.name != 'profiles/default.jpg':
                file_path = self.profile_picture.path
                if os.path.isfile(file_path):
                    os.remove(file_path)
                folder = os.path.dirname(file_path)
                if os.path.isdir(folder) and not os.listdir(folder):
                    shutil.rmtree(folder)
        except Exception:
            # Never block user deletion/anonymization on file system errors
            pass

    def delete(self, *args, **kwargs):
        # Hard delete: remove DB row and any stored files belonging to this user
        self._remove_profile_picture_file()
        super().delete(*args, **kwargs)
    
    def anonymize(self):
        # GDPR-friendly alternative: scrub personal data, deactivate account, release personal identifiers while keeping referential integrity for related objects

        # Clean profile picture and reset to default
        self._remove_profile_picture_file()
        self.profile_picture = 'profiles/default.jpg'

        # Replace PII with non-identifying placeholders that remain unique
        unique_suffix = uuid4().hex[:12]
        self.email = f"deleted_{self.pk}_{unique_suffix}#example.invalid"
        self.username = f"deleted_user_{self.pk}_{unique_suffix}"
        self.first_name = "Deleted"
        self.last_name = "User"
        self.bio = None
        self.date_of_birth = None

        # Reset verification and login-related attributes
        self.is_email_verified = False
        self.email_verification_code = None
        self.verification_code_sent_at = None
        self.ip_address = None
        self.last_login_ip = None
        self.is_online = False
        self.is_active = False # Important -> prevent further logins

        # Mark anonymized
        self.is_anonymized = True
        self.save(update_fields=[
            'profile_picture', 'email', 'username', 'first_name', 'last_name',
            'bio', 'date_of_birth', 'is_email_verified', 'email_verification_code',
            'verification_code_sent_at', 'ip_address', 'last_login_ip', 'is_online',
            'is_active', 'is_anonymized'
        ])


    def generate_verification_code(self):
        # Generate a 6 numbers code and link it with user
        self.email_verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.verification_code_sent_at = timezone.now()
        self.save()
        return self.email_verification_code
    
    def can_send_verification_code(self):
        # Check if a new code can be send
        # Return True if no code was sent or  more than two minutes have passed
        if not self.verification_code_sent_at:
            return True
        
        time_since_last_last_code = timezone.now() - self.verification_code_sent_at
        return time_since_last_last_code.total_seconds() >= 15 # Two minutes in seconds
    
    def is_verification_code_valid(self, code):
        if not self.email_verification_code or not self.verification_code_sent_at:
            return False
        
        if self.email_verification_code != code:
            return False
        
        # Check if the code has not expired (10 minutes)
        time_since_sent = timezone.now() - self.verification_code_sent_at
        return time_since_sent.total_seconds() <= 600
    
    def verify_email(self, code):
        # If code is valid, marks email as verified and clean up temporary data
        if self.is_verification_code_valid(code):
            self.is_email_verified = True
            self.email_verification_code = ''
            self.verification_code_sent_at = None
            self.save(update_fields=['is_email_verified', 'email_verification_code', 'verification_code_sent_at'])
            return True
        return False
    
    def send_verification_email(self):
        if not self.can_send_verification_code():
            return False, "You have to wait 2 minutes before asking a new code"
        
        code = self.generate_verification_code()

        subject = 'Email verification'
        message = f"""Hello {self.first_name}, Thanks for creating a account on Shuttrly!
        Your code is {code}"""

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently = False
            )
            return True, "Code sent successfully!"
        except Exception as e:
            return False, f"Error : {str(e)}"