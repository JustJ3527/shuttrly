from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class SuperuserUsernameBackend(ModelBackend):
    """
    Custom authentication backend:
    - Allows all users to log in using their username (case-insensitive)
    - Regular users can also use their email (as USERNAME_FIELD = 'email')
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch user by username (case-insensitive)
            user = UserModel.objects.get(username__iexact=username)
            if user.check_password(password) and user.is_active:
                return user
        except UserModel.DoesNotExist:
            pass

        # Fall back to default: try email (case-insensitive)
        try:
            user = UserModel.objects.get(email__iexact=username)
            if user.check_password(password) and user.is_active:
                return user
        except UserModel.DoesNotExist:
            return None

        return None