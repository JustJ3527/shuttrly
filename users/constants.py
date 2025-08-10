"""
Constants for user authentication, 2FA, and email timing.
Centralized configuration for all timeout values.
"""

# Email code timing constants
EMAIL_CODE_RESEND_DELAY_SECONDS = 20
EMAIL_CODE_EXPIRY_SECONDS = 600  # 10 minutes

# 2FA specific timing
TOTP_WINDOW_SIZE = 1  # Time window for TOTP validation
TOTP_STEP_SECONDS = 30  # TOTP step size

# Session timeout constants
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
TRUSTED_DEVICE_EXPIRY_DAYS = 30  # 30 days

# Rate limiting constants
MAX_LOGIN_ATTEMPTS = 5
MAX_2FA_ATTEMPTS = 3
LOGIN_COOLDOWN_SECONDS = 300  # 5 minutes

# Email verification constants
EMAIL_VERIFICATION_EXPIRY_HOURS = 24  # 24 hours
