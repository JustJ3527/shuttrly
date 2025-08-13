# users/middleware.py

from django.utils import timezone
from datetime import timedelta
from django.contrib import messages


class OnlineStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user = request.user
            if not user.is_online:
                user.is_online = True
                user.save(update_fields=["is_online"])

        response = self.get_response(request)

        # Let the JavaScript MessageManager handle message lifecycle
        # No need to clear messages here as they are handled client-side

        return response


class LoginCachePreventionMiddleware:
    """
    Middleware to prevent caching on login pages and avoid reload warnings.

    This middleware adds appropriate headers to prevent browsers from caching
    login pages, which can cause the "form resubmission" warning when reloading.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is a login-related page
        if self._is_login_page(request):
            # Add headers to prevent caching and avoid reload warnings
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            # Additional header to prevent form resubmission
            response["X-Content-Type-Options"] = "nosniff"

        return response

    def _is_login_page(self, request):
        """
        Check if the current request is for a login-related page.
        """
        # Check URL patterns
        login_patterns = ["/login/", "/register/", "/2fa/"]
        current_path = request.path_info.lower()

        for pattern in login_patterns:
            if pattern in current_path:
                return True

        # Check if user is not authenticated and on a login-related view
        if not request.user.is_authenticated:
            # You can add more specific checks here if needed
            return True

        return False
