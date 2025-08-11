# users/models.py - Version corrigée
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone
import os
import shutil
from django.conf import settings
from uuid import uuid4
from PIL import Image
import random
from django.core.mail import send_mail
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError

from .constants import EMAIL_CODE_EXPIRY_SECONDS


def user_directory_path(instance, filename):
    ext = filename.split(".")[-1]
    unique_id = uuid4().hex
    filename = f"{unique_id}.{ext}"
    return os.path.join("profiles", unique_id, filename)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        is_superuser = extra_fields.get("is_superuser", False)

        if not is_superuser and not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")

        # Enforce name fields only for non-superuser
        if not is_superuser:
            if not extra_fields.get("first_name"):
                raise ValueError("First name is required")
            if not extra_fields.get("last_name"):
                raise ValueError("Last name is required")

        email = self.normalize_email(email)

        # Ensure explicit flags exist
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_email_verified", False)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save()
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        # Fill defaults for superuser
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        extra_fields["is_email_verified"] = True

        # Allow blank names for superusers
        extra_fields.setdefault("first_name", "")
        extra_fields.setdefault("last_name", "")

        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    def save(self, *args, **kwargs):
        # Validate the model before saving
        self.clean()

        # Keep track of the previous profile picture path for delayed deletion
        old_profile_picture_path = None
        try:
            if self.pk:  # Only for existing users
                old_user = CustomUser.objects.get(pk=self.pk)
                if (
                    old_user.profile_picture
                    and old_user.profile_picture.name != "profiles/default.jpg"
                ):
                    old_profile_picture_path = old_user.profile_picture.name
        except CustomUser.DoesNotExist:
            old_profile_picture_path = None

        super().save(*args, **kwargs)  # Save the user first

        # If the photo changed and is not the default image, schedule old file for deletion
        if (
            old_profile_picture_path
            and self.profile_picture
            and old_profile_picture_path != self.profile_picture.name
        ):

            # Import here to avoid circular imports
            from .utils import schedule_profile_picture_deletion

            delay = getattr(settings, "PROFILE_PICTURE_DELETION_DELAY_SECONDS", 86400)

            schedule_profile_picture_deletion(old_profile_picture_path, seconds=delay)
            print(
                f"🗓️ Scheduled deletion of old profile picture: {old_profile_picture_path}"
            )

        # Resize the new image (if not default)
        if self.profile_picture and self.profile_picture.name != "profiles/default.jpg":
            try:
                img = Image.open(self.profile_picture.path)

                max_size = (450, 450)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Extract lowercase extension
                ext = os.path.splitext(self.profile_picture.name)[1].lower()
                format_map = {
                    ".jpg": "JPEG",
                    ".jpeg": "JPEG",
                    ".png": "PNG",
                    ".gif": "GIF",
                    ".bmp": "BMP",
                    ".tiff": "TIFF",
                }
                img_format = format_map.get(ext, "JPEG")
                img.save(
                    self.profile_picture.path,
                    format=img_format,
                    optimize=True,
                    quality=70,
                )
            except Exception as e:
                print(f"⚠️ Error resizing image: {e}")

    # Basic identity fields
    email = models.EmailField(unique=True, blank=True, null=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Optional fields
    bio = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to=user_directory_path, default="profiles/default.jpg"
    )

    # IP tracking
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    # Permissions and status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_date = models.DateTimeField(blank=True, null=True)
    is_online = models.BooleanField(default=False)

    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_sent_at = models.DateTimeField(blank=True, null=True)

    # --- 2FA Email ---
    email_2fa_enabled = models.BooleanField(default=False)
    email_2fa_code = models.CharField(max_length=6, blank=True, null=True)
    email_2fa_sent_at = models.DateTimeField(blank=True, null=True)

    # --- 2FA TOTP ---
    totp_enabled = models.BooleanField(default=False)
    twofa_totp_secret = models.CharField(max_length=64, blank=True, null=True)

    # GDPR (=RGPD) / alternative to hard delete
    is_anonymized = models.BooleanField(default=False)

    # Link the custom manager
    objects = CustomUserManager()

    # Main authentication field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.username

    def clean(self):
        """Validate the model data before saving"""
        from .validators import UsernameValidator

        super().clean()

        # Validate username using the same validator as forms
        if self.username:
            validator = UsernameValidator()
            try:
                validator.validate(self.username)
            except ValidationError as e:
                raise ValidationError({"username": e})

    def _remove_profile_picture_file(self):
        """Remove profile picture file immediately (for deletion/anonymization)"""
        try:
            if (
                self.profile_picture
                and self.profile_picture.name
                and self.profile_picture.name != "profiles/default.jpg"
            ):
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
        # GDPR-friendly alternative: scrub personal data, deactivate account
        self._remove_profile_picture_file()
        self.profile_picture = "profiles/default.jpg"

        # Replace PII with non-identifying placeholders that remain unique
        unique_suffix = uuid4().hex[:12]
        self.email = f"deleted_{self.pk}_{unique_suffix}@example.invalid"
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
        self.is_active = False

        # Mark anonymized
        self.is_anonymized = True
        self.save(
            update_fields=[
                "profile_picture",
                "email",
                "username",
                "first_name",
                "last_name",
                "bio",
                "date_of_birth",
                "is_email_verified",
                "email_verification_code",
                "verification_code_sent_at",
                "ip_address",
                "last_login_ip",
                "is_online",
                "is_active",
                "is_anonymized",
            ]
        )

    def generate_verification_code(self):
        self.email_verification_code = "".join(
            [str(random.randint(0, 9)) for _ in range(6)]
        )
        self.verification_code_sent_at = timezone.now()
        self.save()
        return self.email_verification_code

    def can_send_verification_code(self):
        if not self.verification_code_sent_at:
            return True

        time_since_last_code = timezone.now() - self.verification_code_sent_at
        return time_since_last_code.total_seconds() >= 15

    def is_verification_code_valid(self, code):
        if not self.email_verification_code or not self.verification_code_sent_at:
            return False

        if self.email_verification_code != code:
            return False

        # Check if the code has not expired (10 minutes)
        time_since_sent = timezone.now() - self.verification_code_sent_at
        return time_since_sent.total_seconds() <= EMAIL_CODE_EXPIRY_SECONDS

    def verify_email(self, code):
        if self.is_verification_code_valid(code):
            self.is_email_verified = True
            self.email_verification_code = ""
            self.verification_code_sent_at = None
            self.save(
                update_fields=[
                    "is_email_verified",
                    "email_verification_code",
                    "verification_code_sent_at",
                ]
            )
            return True
        return False

    def send_verification_email(self):
        if not self.can_send_verification_code():
            return False, "You have to wait 2 minutes before asking a new code"

        code = self.generate_verification_code()

        subject = "Email verification"
        message = f"""Hello {self.first_name}, Thanks for creating a account on Shuttrly!
        Your code is {code}"""

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=False,
            )
            return True, "Code sent successfully!"
        except Exception as e:
            return False, f"Error : {str(e)}"


class PendingFileDeletion(models.Model):
    file_path = models.CharField(max_length=500)
    trash_path = models.CharField(max_length=500, blank=True)
    scheduled_deletion = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default="profile_picture_change")

    class Meta:
        indexes = [
            models.Index(fields=["scheduled_deletion"]),
        ]

    def __str__(self):
        return f"Delete {self.file_path} on {self.scheduled_deletion}"

    def move_to_trash(self):
        """Déplace le fichier vers un dossier trash"""
        if not self.trash_path and default_storage.exists(self.file_path):
            # Créer le chemin trash
            trash_dir = os.path.join("trash", "profile_pictures")
            filename = os.path.basename(self.file_path)
            timestamp = self.created_at.strftime("%Y%m%d_%H%M%S")
            trash_filename = f"{timestamp}_{filename}"
            self.trash_path = os.path.join(trash_dir, trash_filename)

            # Créer le dossier trash si nécessaire
            trash_full_path = os.path.join(settings.MEDIA_ROOT, trash_dir)
            os.makedirs(trash_full_path, exist_ok=True)

            # Déplacer le fichier
            old_path = os.path.join(settings.MEDIA_ROOT, self.file_path)
            new_path = os.path.join(settings.MEDIA_ROOT, self.trash_path)
            shutil.move(old_path, new_path)

            self.save()
            return True
        return False


class TrustedDevice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trusted_devices",
    )
    device_token = models.CharField(max_length=64, unique=True)
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # Analyzed device information
    device_type = models.CharField(max_length=50, blank=True, null=True)
    device_family = models.CharField(max_length=100, blank=True, null=True)
    browser_family = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=50, blank=True, null=True)
    os_family = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.device_token[:8]}..."
