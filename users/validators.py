import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UsernameValidator:
    """
    Comprehensive username validator that enforces:
    - Length constraints (3-30 characters)
    - Allowed characters (letters, numbers, underscores)
    - Cannot start with numbers or underscores
    - Cannot end with underscores
    - No consecutive underscores
    """

    def __init__(self, min_length=3, max_length=30):
        self.min_length = min_length
        self.max_length = max_length

    def __call__(self, username):
        """Make the validator callable for Django forms"""
        return self.validate(username)

    def validate(self, username):
        if not username:
            raise ValidationError(_("Username is required."), code="username_required")

        # Convert to lowercase and strip whitespace
        username = username.strip().lower()

        # Check length
        if len(username) < self.min_length:
            raise ValidationError(
                _("Username must be at least {min_length} characters long.").format(
                    min_length=self.min_length
                ),
                code="username_too_short",
            )

        if len(username) > self.max_length:
            raise ValidationError(
                _("Username cannot exceed {max_length} characters.").format(
                    max_length=self.max_length
                ),
                code="username_too_long",
            )

        # Check allowed characters
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError(
                _("Username can only contain letters, numbers, and underscores."),
                code="username_invalid_characters",
            )

        # Check cannot start with numbers or underscores
        if re.match(r"^[0-9_]", username):
            raise ValidationError(
                _("Username cannot start with numbers or underscores."),
                code="username_invalid_start",
            )

        # Check cannot end with underscores
        if username.endswith("_"):
            raise ValidationError(
                _("Username cannot end with an underscore."),
                code="username_invalid_end",
            )

        # Check no consecutive underscores
        if "__" in username:
            raise ValidationError(
                _("Username cannot contain consecutive underscores."),
                code="username_consecutive_underscores",
            )

    def get_help_text(self):
        return _(
            "Username must be {min_length}-{max_length} characters long, "
            "contain only letters, numbers, and underscores. "
            "Cannot start with numbers or underscores, "
            "cannot end with underscores, "
            "and cannot contain consecutive underscores."
        ).format(min_length=self.min_length, max_length=self.max_length)


class CustomPasswordValidator:
    def __init__(
        self,
        min_length=12,
        require_uppercase=True,
        require_lowercase=True,
        require_digits=True,
        require_symbol=True,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_symbol = require_symbol

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least {min_length} characters long."),
                code="password_too_short",
            )

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code="missing_uppercase",
            )

        if self.require_lowercase and not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code="missing_lowercase",
            )

        if self.require_digits and not re.search(r"\d", password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code="missing_digit",
            )

        if self.require_symbol and not re.search(
            r"[!@#$%^&*()_+{}\[\]:;<>,.?~\\/-]", password
        ):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code="missing_symbol",
            )

    def get_help_text(self):
        parts = [f"at least {self.min_length} characters long"]
        if self.require_uppercase:
            parts.append(" one uppercase letter")
        if self.require_lowercase:
            parts.append(" one lowercase letter")
        if self.require_digits:
            parts.append(" one digit")
        if self.require_symbol:
            parts.append(" one special character")
        return _("Your password must contain " + ",".join(parts) + ".")
