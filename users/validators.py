import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


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
