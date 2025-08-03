from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.


class UserLog(models.Model):
    ACTIONS = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("update_profile", "Update Profile"),
        ("delete_account", "Delete Account"),
        ("register", "Register"),
        ("verify_email", "Email Verified"),
        # Add more actions
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="logs_user_logs",
    )
    action = models.CharField(max_length=30, choices=ACTIONS)
    timestamp = models.DateTimeField(default=timezone.now)
    extra_info = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} @ {self.timestamp}"
