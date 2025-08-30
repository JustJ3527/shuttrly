"""
Structured error handling for authentication API
Provides consistent error responses with error codes and user-friendly messages
"""

from rest_framework import status
from rest_framework.response import Response
from typing import Dict, Any, Optional, Union
from django.core.exceptions import ValidationError


class AuthErrorCode:
    """Authentication error codes for consistent error handling"""
    
    # Login errors
    INVALID_CREDENTIALS = "AUTH_001"
    USER_NOT_FOUND = "AUTH_002"
    ACCOUNT_LOCKED = "AUTH_003"
    EMAIL_NOT_VERIFIED = "AUTH_004"
    TOO_MANY_ATTEMPTS = "AUTH_005"
    
    # Registration errors
    EMAIL_ALREADY_EXISTS = "AUTH_101"
    USERNAME_ALREADY_TAKEN = "AUTH_102"
    INVALID_USERNAME_FORMAT = "AUTH_103"
    INVALID_PASSWORD_FORMAT = "AUTH_104"
    PASSWORDS_DONT_MATCH = "AUTH_105"
    AGE_RESTRICTION = "AUTH_106"
    VERIFICATION_CODE_EXPIRED = "AUTH_107"
    INVALID_VERIFICATION_CODE = "AUTH_108"
    
    # 2FA errors
    TWOFA_REQUIRED = "AUTH_201"
    INVALID_2FA_CODE = "AUTH_202"
    TWOFA_CODE_EXPIRED = "AUTH_203"
    TWOFA_METHOD_NOT_AVAILABLE = "AUTH_204"
    
    # General errors
    VALIDATION_ERROR = "AUTH_301"
    SERVER_ERROR = "AUTH_302"
    NETWORK_ERROR = "AUTH_303"
    SESSION_EXPIRED = "AUTH_304"


class AuthErrorMessage:
    """User-friendly error messages for authentication errors"""
    
    # Login messages
    INVALID_CREDENTIALS = "Invalid email/username or password. Please check your credentials and try again."
    USER_NOT_FOUND = "No account found with this email/username. Please check your input or create a new account."
    ACCOUNT_LOCKED = "Your account has been temporarily locked due to too many failed login attempts. Please try again later."
    EMAIL_NOT_VERIFIED = "Please verify your email address before logging in. Check your inbox for a verification link."
    TOO_MANY_ATTEMPTS = "Too many failed login attempts. Please wait a few minutes before trying again."
    
    # Registration messages
    EMAIL_ALREADY_EXISTS = "An account with this email address already exists. Please use a different email or try logging in."
    USERNAME_ALREADY_TAKEN = "This username is already taken. Please choose a different username."
    INVALID_USERNAME_FORMAT = "Username must be 3-30 characters long and can only contain letters, numbers, and underscores."
    INVALID_PASSWORD_FORMAT = "Password must be at least 8 characters long and contain a mix of letters, numbers, and symbols."
    PASSWORDS_DONT_MATCH = "Passwords do not match. Please make sure both passwords are identical."
    AGE_RESTRICTION = "You must be at least 16 years old to create an account."
    VERIFICATION_CODE_EXPIRED = "Verification code has expired. Please request a new code."
    INVALID_VERIFICATION_CODE = "Invalid verification code. Please check your email and enter the correct code."
    
    # 2FA messages
    TWOFA_REQUIRED = "Two-factor authentication is required for your account."
    INVALID_2FA_CODE = "Invalid 2FA code. Please check your authenticator app or email and try again."
    TWOFA_CODE_EXPIRED = "2FA code has expired. Please request a new code."
    TWOFA_METHOD_NOT_AVAILABLE = "The selected 2FA method is not available for your account."
    
    # General messages
    VALIDATION_ERROR = "Please check your input and try again."
    SERVER_ERROR = "An error occurred on our servers. Please try again later."
    NETWORK_ERROR = "Network connection error. Please check your internet connection and try again."
    SESSION_EXPIRED = "Your session has expired. Please log in again."


class AuthErrorResponse:
    """Structured error response for authentication API"""
    
    @staticmethod
    def create(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST
    ) -> Response:
        """
        Create a structured error response
        
        Args:
            error_code: Unique error identifier (e.g., AUTH_001)
            message: User-friendly error message
            details: Additional error details (optional)
            http_status: HTTP status code
            
        Returns:
            Response object with structured error format
        """
        error_response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "type": "authentication_error"
            }
        }
        
        if details:
            error_response["error"]["details"] = details
            
        return Response(error_response, status=http_status)
    
    @staticmethod
    def invalid_credentials(details: Optional[Dict[str, Any]] = None) -> Response:
        """Invalid email/username or password"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.INVALID_CREDENTIALS,
            message=AuthErrorMessage.INVALID_CREDENTIALS,
            details=details,
            http_status=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def user_not_found(identifier: str) -> Response:
        """No user found with the provided identifier"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.USER_NOT_FOUND,
            message=AuthErrorMessage.USER_NOT_FOUND,
            details={"identifier": identifier},
            http_status=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def account_locked(lockout_until: Optional[str] = None) -> Response:
        """Account temporarily locked"""
        details = {}
        if lockout_until:
            details["lockout_until"] = lockout_until
            
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.ACCOUNT_LOCKED,
            message=AuthErrorMessage.ACCOUNT_LOCKED,
            details=details,
            http_status=status.HTTP_423_LOCKED
        )
    
    @staticmethod
    def email_not_verified(email: str) -> Response:
        """Email address not verified"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.EMAIL_NOT_VERIFIED,
            message=AuthErrorMessage.EMAIL_NOT_VERIFIED,
            details={"email": email},
            http_status=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def too_many_attempts(attempts_remaining: int = 0) -> Response:
        """Too many failed login attempts"""
        details = {}
        if attempts_remaining > 0:
            details["attempts_remaining"] = attempts_remaining
            
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.TOO_MANY_ATTEMPTS,
            message=AuthErrorMessage.TOO_MANY_ATTEMPTS,
            details=details,
            http_status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    @staticmethod
    def email_already_exists(email: str) -> Response:
        """Email already registered"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.EMAIL_ALREADY_EXISTS,
            message=AuthErrorMessage.EMAIL_ALREADY_EXISTS,
            details={"email": email},
            http_status=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def username_already_taken(username: str) -> Response:
        """Username already taken"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.USERNAME_ALREADY_TAKEN,
            message=AuthErrorMessage.USERNAME_ALREADY_TAKEN,
            details={"username": username},
            http_status=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def invalid_username_format(username: str, validation_errors: Optional[list] = None) -> Response:
        """Invalid username format"""
        details = {"username": username}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.INVALID_USERNAME_FORMAT,
            message=AuthErrorMessage.INVALID_USERNAME_FORMAT,
            details=details,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def invalid_password_format(validation_errors: Optional[list] = None) -> Response:
        """Invalid password format"""
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.INVALID_PASSWORD_FORMAT,
            message=AuthErrorMessage.INVALID_PASSWORD_FORMAT,
            details=details,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def passwords_dont_match() -> Response:
        """Passwords don't match"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.PASSWORDS_DONT_MATCH,
            message=AuthErrorMessage.PASSWORDS_DONT_MATCH,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def age_restriction(minimum_age: int = 16) -> Response:
        """User too young to register"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.AGE_RESTRICTION,
            message=AuthErrorMessage.AGE_RESTRICTION,
            details={"minimum_age": minimum_age},
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def verification_code_expired() -> Response:
        """Verification code has expired"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.VERIFICATION_CODE_EXPIRED,
            message=AuthErrorMessage.VERIFICATION_CODE_EXPIRED,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def invalid_verification_code() -> Response:
        """Invalid verification code"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.INVALID_VERIFICATION_CODE,
            message=AuthErrorMessage.INVALID_VERIFICATION_CODE,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def twofa_required() -> Response:
        """2FA is required"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.TWOFA_REQUIRED,
            message=AuthErrorMessage.TWOFA_REQUIRED,
            http_status=status.HTTP_200_OK  # 200 because this is expected behavior
        )
    
    @staticmethod
    def invalid_2fa_code() -> Response:
        """Invalid 2FA code"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.INVALID_2FA_CODE,
            message=AuthErrorMessage.INVALID_2FA_CODE,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def twofa_code_expired() -> Response:
        """2FA code has expired"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.TWOFA_CODE_EXPIRED,
            message=AuthErrorMessage.TWOFA_CODE_EXPIRED,
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def twofa_method_not_available(method: str) -> Response:
        """2FA method not available"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.TWOFA_METHOD_NOT_AVAILABLE,
            message=AuthErrorMessage.TWOFA_METHOD_NOT_AVAILABLE,
            details={"method": method},
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def validation_error(validation_errors: Dict[str, Any]) -> Response:
        """General validation error"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.VALIDATION_ERROR,
            message=AuthErrorMessage.VALIDATION_ERROR,
            details={"validation_errors": validation_errors},
            http_status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def server_error(details: Optional[Dict[str, Any]] = None) -> Response:
        """Server error"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.SERVER_ERROR,
            message=AuthErrorMessage.SERVER_ERROR,
            details=details,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def network_error() -> Response:
        """Network error"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.NETWORK_ERROR,
            message=AuthErrorMessage.NETWORK_ERROR,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @staticmethod
    def session_expired() -> Response:
        """Session expired"""
        return AuthErrorResponse.create(
            error_code=AuthErrorCode.SESSION_EXPIRED,
            message=AuthErrorMessage.SESSION_EXPIRED,
            http_status=status.HTTP_401_UNAUTHORIZED
        )


def handle_authentication_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Response:
    """
    Generic error handler for authentication errors
    
    Args:
        error: The exception that occurred
        context: Additional context about the error
        
    Returns:
        Response object with appropriate error details
    """
    if isinstance(error, ValidationError):
        return AuthErrorResponse.validation_error({"validation_errors": str(error)})
    elif "credentials" in str(error).lower():
        return AuthErrorResponse.invalid_credentials()
    elif "not found" in str(error).lower():
        return AuthErrorResponse.user_not_found("unknown")
    else:
        return AuthErrorResponse.server_error({"error": str(error)})
