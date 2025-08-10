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
