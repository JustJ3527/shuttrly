"""  """

# Standard library imports
from datetime import datetime

# Third party imports
from django.contrib.auth import authenticate
from django.forms import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

# Local imports
from users.models import CustomUser
from users.utils import calculate_age
from users.validators import UsernameValidator, CustomPasswordValidator
from users.api.errors import AuthErrorResponse, AuthErrorCode


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data (without sensitive information)"""
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'date_of_birth', 'bio', 'is_private', 'profile_picture', 
            'is_email_verified', 'date_joined', 'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'is_email_verified', 'is_active']

# ===============================
# REGISTRATION
# ===============================

class RegisterStep1Serializer(serializers.Serializer):
    """Step 1: Email"""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Check if email already exists
        if CustomUser.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                AuthErrorResponse.email_already_exists(value).data["error"]["message"]
            )
        return value

class RegisterStep2Serializer(serializers.Serializer):
    """Step 2: Verification code"""
    verification_code = serializers.CharField(max_length=6, min_length=6)

class RegisterStep3Serializer(serializers.Serializer):
    """Step 3: Personal information"""
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=40)
    date_of_birth = serializers.DateField()
    
    def validate_date_of_birth(self, value):
        age = calculate_age(value)
        if age < 16:
            raise serializers.ValidationError(
                AuthErrorResponse.age_restriction().data["error"]["message"]
            )
        return value

class RegisterStep4Serializer(serializers.Serializer):
    """Step 4: Username"""
    username = serializers.CharField(max_length=30)
    
    def validate_username(self, value):
        validator = UsernameValidator()
        try:
            validator.validate(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        # Check availability
        if CustomUser.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError(
                AuthErrorResponse.username_already_taken(value).data["error"]["message"]
            )
        
        return value.lower()

class RegisterStep5Serializer(serializers.Serializer):
    """Step 5: Password"""
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 != password2:
            raise serializers.ValidationError(
                AuthErrorResponse.passwords_dont_match().data["error"]["message"]
            )
        
        # Validate password strength
        validator = CustomPasswordValidator()
        try:
            validator.validate(password1)
        except ValidationError as e:
            raise serializers.ValidationError(
                AuthErrorResponse.invalid_password_format([str(e)]).data["error"]["message"]
            )
        
        return data

# ===============================
# PROFILE
# ===============================
class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    identifier = serializers.CharField(max_length=255) # email or username
    password = serializers.CharField(write_only=True)
    remember_device = serializers.BooleanField(default=False)

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        # Authenticate the user
        user = authenticate(username=identifier, password=password)

        if not user:
            raise serializers.ValidationError(
                AuthErrorResponse.invalid_credentials().data["error"]["message"]
            )

        if not user.is_email_verified:
            raise serializers.ValidationError(
                AuthErrorResponse.email_not_verified(identifier).data["error"]["message"]
            )

        data["user"] =  user
        return data

class EmailVerificationSerializer(serializers.Serializer):
    """Email verification code"""
    code = serializers.CharField(max_length=6, min_length=6)

class ResendCodeSerializer(serializers.Serializer):
    """Resend verification code"""
    email = serializers.EmailField()

class TokenResponseSerializer(serializers.Serializer):
    """Token response serializer"""
    access = serializers.CharField(max_length=255)
    refresh = serializers.CharField(max_length=255)
    user = UserSerializer()

def create_tokens_for_user(user):
    """Create token for user"""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }