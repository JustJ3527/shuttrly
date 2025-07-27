from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
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
    # Basic identidy fields
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    date_of_birth = models.DateField()

    #Optional fields
    bio = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    # IP tracking
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    # Permissions and status
    is_active = models.BooleanField(default=True) #Can the user log in?
    is_staff = models.BooleanField(default=False) #Can the user access the admin site?
    date_joined = models.DateTimeField(default=timezone.now) #When the user registered
    last_login_date = models.DateTimeField(blank=True, null=True) #Last login time
    
    # Link the custom manager
    objects = CustomUserManager()

    # Main authentication field
    USERNAME_FIELD = 'email' #Used to log in
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'date_of_birth'] 
    
    def __str__( self):
        return self.username #Used in admin and shell
