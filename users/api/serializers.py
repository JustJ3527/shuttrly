"""User API serializers for data validation and transformation"""

# Standard library imports
from datetime import datetime

# Third party imports
from rest_framework import serializers

# Local imports
from users.models import CustomUser
from users.validators import UsernameValidator, CustomPasswordValidator


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
# REGISTRATION SERIALIZERS
# ===============================

class RegisterStep1Serializer(serializers.Serializer):
    """Step 1: Email validation"""
    email = serializers.EmailField()


class RegisterStep2Serializer(serializers.Serializer):
    """Step 2: Verification code validation"""
    verification_code = serializers.CharField(max_length=6, min_length=6)


class RegisterStep3Serializer(serializers.Serializer):
    """Step 3: Personal information validation"""
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=40)
    date_of_birth = serializers.DateField()


class RegisterStep4Serializer(serializers.Serializer):
    """Step 4: Username validation"""
    username = serializers.CharField(max_length=30)
    
    def validate_username(self, value):
        """Validate username format and convert to lowercase"""
        validator = UsernameValidator()
        try:
            validator.validate(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value.lower()


class RegisterStep5Serializer(serializers.Serializer):
    """Step 5: Password validation"""
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validate password match and strength"""
        password1 = data.get('password1')
        password2 = data.get('password2')

        if password1 != password2:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        validator = CustomPasswordValidator()
        try:
            validator.validate(password1)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        return data


# ===============================
# LOGIN SERIALIZERS
# ===============================

class LoginSerializer(serializers.Serializer):
    """Login credentials validation"""
    identifier = serializers.CharField(max_length=255)  # email or username
    password = serializers.CharField(write_only=True)
    remember_device = serializers.BooleanField(default=False)


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification code validation"""
    code = serializers.CharField(max_length=6, min_length=6)


class ResendCodeSerializer(serializers.Serializer):
    """Resend verification code validation"""
    email = serializers.EmailField()


class TokenResponseSerializer(serializers.Serializer):
    """Token response serializer"""
    access = serializers.CharField(max_length=255)
    refresh = serializers.CharField(max_length=255)
    user = UserSerializer()


# ===============================
# 2FA SERIALIZERS
# ===============================

class TwoFAMethodChoiceSerializer(serializers.Serializer):
    """2FA method choice validation"""
    chosen_method = serializers.ChoiceField(choices=['email', 'totp'])


class Email2FASerializer(serializers.Serializer):
    """Email 2FA code validation"""
    verification_code = serializers.CharField(max_length=6, min_length=6)
    resend_code = serializers.BooleanField(required=False, default=False)


class TOTP2FASerializer(serializers.Serializer):
    """TOTP 2FA code validation"""
    totp_code = serializers.CharField(max_length=6, min_length=6)


# ===============================
# PROFILE UPDATE SERIALIZERS
# ===============================

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Profile update validation"""
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'bio', 'is_private',
            'current_password', 'new_password'
        ]
    
    def validate_username(self, value):
        """Validate username format and convert to lowercase"""
        validator = UsernameValidator()
        try:
            validator.validate(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value.lower()


# ===============================
# UTILITY FUNCTIONS
# ===============================

def create_tokens_for_user(user):
    """Create JWT tokens for user"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }