# Standard library imports
from datetime import datetime, date, timedelta
import uuid

# Third party imports
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

# Local imports
from users.models import CustomUser
from users.validators import UsernameValidator
from users.utils import (
    generate_email_code, send_verification_email,
    get_client_ip, get_user_agent, get_location_from_ip,
    send_2FA_email, verify_totp, is_trusted_device,
    initialize_login_session_data, login_success, calculate_age
)
from users.constants import EMAIL_CODE_RESEND_DELAY_SECONDS, EMAIL_CODE_EXPIRY_SECONDS
from logs.utils import log_user_action_json

from users.api.serializers import (
    RegisterStep1Serializer, RegisterStep2Serializer, RegisterStep3Serializer,
    RegisterStep4Serializer, RegisterStep5Serializer, LoginSerializer, ResendCodeSerializer, 
    UserSerializer, TwoFAMethodChoiceSerializer, Email2FASerializer, TOTP2FASerializer,
    ProfileUpdateSerializer, create_tokens_for_user
)
from users.api.errors import AuthErrorResponse, handle_authentication_error

# ===============================
# REGISTRATION API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_step_1_email(request):
    """Step 1: Email verification and sending code"""
    serializer = RegisterStep1Serializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    email = serializer.validated_data['email']
    
    # Check if email already exists for active users
    if CustomUser.objects.filter(email=email, is_active=True).exists():
        return AuthErrorResponse.email_already_exists(email)
    
    # Clean temporary users with this email
    CustomUser.objects.filter(email=email, is_active=False).delete()
    
    # Generate verification code
    verification_code = generate_email_code()
    
    # Create temporary user
    temp_username = f"temp_{uuid.uuid4().hex[:8]}"
    while CustomUser.objects.filter(username=temp_username).exists():
        temp_username = f"temp_{uuid.uuid4().hex[:8]}"
    
    try:
        temp_user = CustomUser.objects.create(
            email=email,
            username=temp_username,
            first_name="",
            last_name="",
            is_active=False,
            email_verification_code=verification_code,
            verification_code_sent_at=timezone.now()
        )
        
        # Send verification email
        success = send_verification_email(email, verification_code)
        
        if success:
            return Response({
                'success': True,
                'message': f"Verification code sent to your email: {email}",
                'email': email,
                'temp_user_id': temp_user.id
            }, status=status.HTTP_200_OK)
        else:
            # Clean up if email sending failed
            temp_user.delete()
            return AuthErrorResponse.server_error({
                'email': email,
                'error': 'Failed to send verification code'
            })
            
    except Exception as e:
        return AuthErrorResponse.server_error({
            'email': email,
            'error': f'Error creating temporary user: {str(e)}'
        })

@api_view(['POST'])
@permission_classes([AllowAny])
def register_step_2_verifify_email(request):
    """Step 2: Verify email"""
    serializer = RegisterStep2Serializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    email = request.data.get("email")
    submitted_code = serializer.validated_data["verification_code"]
    
    if not email:
        return AuthErrorResponse.validation_error({
            'email': ['Email is required for verification']
        })
    
    try:
        temp_user = CustomUser.objects.get(email=email, is_active=False)
        
        # Check code expiration
        if temp_user.verification_code_sent_at:
            time_since_sent = timezone.now() - temp_user.verification_code_sent_at
            if time_since_sent.total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:
                return AuthErrorResponse.verification_code_expired()
        
        # Check verification code
        if temp_user.email_verification_code == submitted_code:
            # Mark email as verified but keep temp user for final registration
            temp_user.is_email_verified = True
            temp_user.save()
            
            return Response({
                "success": True, 
                "message": "Email verification successful",
                "email_verified": True
            }, status=status.HTTP_200_OK)
        else:
            return AuthErrorResponse.invalid_verification_code()
            
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.session_expired()

@api_view(['POST'])
@permission_classes([AllowAny])
def register_complete(request):
    """Complete registration with all required information"""
    email = request.data.get('email')
    
    if not email:
        return AuthErrorResponse.validation_error({
            'email': ['Email is required']
        })
    
    # Validate all required fields
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'username', 'password1', 'password2']
    missing_fields = [field for field in required_fields if not request.data.get(field)]
    
    if missing_fields:
        return AuthErrorResponse.validation_error({
            'missing_fields': missing_fields,
            'message': f'The following fields are required: {", ".join(missing_fields)}'
        })
    
    # Check if there's a verified temporary user
    try:
        temp_user = CustomUser.objects.get(email=email, is_active=False, is_email_verified=True)
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.session_expired()
    
    # Validate each step using serializers
    
    step3_data = {
        'first_name': request.data['first_name'],
        'last_name': request.data['last_name'],
        'date_of_birth': request.data['date_of_birth']
    }
    step3_serializer = RegisterStep3Serializer(data=step3_data)
    if not step3_serializer.is_valid():
        return AuthErrorResponse.validation_error(step3_serializer.errors)
    
    # Check age requirement
    try:
        birth_date = datetime.strptime(request.data['date_of_birth'], '%Y-%m-%d').date()
        age = calculate_age(birth_date)
        if age < 16:
            return AuthErrorResponse.age_restriction()
    except ValueError:
        return AuthErrorResponse.validation_error({
            'date_of_birth': ['Invalid date format. Use YYYY-MM-DD']
        })
    
    step4_data = {'username': request.data['username']}
    step4_serializer = RegisterStep4Serializer(data=step4_data)
    if not step4_serializer.is_valid():
        return AuthErrorResponse.validation_error(step4_serializer.errors)
    
    # Check username availability
    if CustomUser.objects.filter(username=request.data['username'].lower(), is_active=True).exists():
        return AuthErrorResponse.username_already_taken(request.data['username'])
    
    step5_data = {
        'password1': request.data['password1'],
        'password2': request.data['password2']
    }
    step5_serializer = RegisterStep5Serializer(data=step5_data)
    if not step5_serializer.is_valid():
        return AuthErrorResponse.validation_error(step5_serializer.errors)
    
    # Create user
    try:
        # Update the existing temporary user
        temp_user.username = request.data['username'].lower()
        temp_user.first_name = request.data['first_name']
        temp_user.last_name = request.data['last_name']
        temp_user.date_of_birth = birth_date
        temp_user.set_password(request.data['password1'])
        temp_user.is_active = True
        temp_user.save()
        
        # Log account creation
        ip = get_client_ip(request)
        temp_user.ip_address = ip
        temp_user.save()
        
        log_user_action_json(
            user=temp_user,
            action="register_api",
            request=request,
            ip_address=ip,
            extra_info={"impacted_user_id": temp_user.id}
        )
        
        # Create JWT tokens
        tokens = create_tokens_for_user(temp_user)
        user_data = UserSerializer(temp_user).data
        
        return Response({
            'success': True,
            'message': 'Account created successfully!',
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return AuthErrorResponse.server_error({
            'error': f'Error creating account: {str(e)}'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_step_4_username(request):
    """Step 4: Username selection with real-time validation"""
    serializer = RegisterStep4Serializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    username = serializer.validated_data['username']
    
    # Check if username is available
    if CustomUser.objects.filter(username=username, is_active=True).exists():
        return AuthErrorResponse.username_already_taken(username)
    
    return Response({
        'success': True,
        'message': 'Username is available.',
        'username': username
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    """Resend a verification code"""
    serializer = ResendCodeSerializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    email = serializer.validated_data['email']
    
    try:
        temp_user = CustomUser.objects.get(email=email, is_active=False)
        
        # Check the time between shipments
        if temp_user.verification_code_sent_at:
            time_since_sent = timezone.now() - temp_user.verification_code_sent_at
            if time_since_sent.total_seconds() < EMAIL_CODE_RESEND_DELAY_SECONDS:
                remaining_time = int(EMAIL_CODE_RESEND_DELAY_SECONDS - time_since_sent.total_seconds())
                return AuthErrorResponse.too_many_attempts(remaining_time)
        
        # Generate and send a new code
        new_code = generate_email_code()
        temp_user.email_verification_code = new_code
        temp_user.verification_code_sent_at = timezone.now()
        temp_user.save()
        
        success = send_verification_email(email, new_code)
        
        if success:
            return Response({
                'success': True,
                'message': 'New verification code sent successfully.'
            }, status=status.HTTP_200_OK)
        else:
            return AuthErrorResponse.server_error({
                'email': email,
                'error': 'Failed to send verification code'
            })
            
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.session_expired()


# ===============================
# LOGIN API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """User login with 2FA support"""
    # Auto-detect step based on request parameters
    if 'identifier' in request.data and 'password' in request.data:
        # Step 1: Credentials
        return handle_login_step_1_credentials_api(request)
    elif 'chosen_method' in request.data:
        # Step 2: 2FA method choice
        return handle_login_step_2_2fa_choice_api(request)
    elif 'verification_code' in request.data:
        # Step 3: Email 2FA
        return handle_login_step_3_email_2fa_api(request)
    elif 'totp_code' in request.data:
        # Step 3: TOTP 2FA
        return handle_login_step_3_totp_2fa_api(request)
    else:
        return AuthErrorResponse.validation_error({
            'request': ['Cannot determine step from parameters']
        })


def handle_login_step_1_credentials_api(request):
    """Step 1: Credentials validation"""
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    identifier = serializer.validated_data['identifier']
    password = serializer.validated_data['password']
    remember_device = serializer.validated_data.get('remember_device', False)
    
    # Authenticate the user
    user = authenticate(username=identifier, password=password)
    
    if not user:
        # Check if user exists to provide appropriate error message
        if CustomUser.objects.filter(username=identifier).exists() or CustomUser.objects.filter(email=identifier).exists():
            return AuthErrorResponse.invalid_credentials()
        else:
            return AuthErrorResponse.user_not_found(identifier)
    
    # Check if email is verified
    if not user.is_email_verified:
        return AuthErrorResponse.email_not_verified(identifier)
    
    # Check if 2FA is required
    if user.email_2fa_enabled or user.totp_enabled:
        # Check if this is a trusted device
        if is_trusted_device(request, user):
            # Trusted device - proceed directly to login
            return handle_login_success_api(request, user, remember_device)
        
        # Not a trusted device - proceed with 2FA
        # Initialize session data
        initialize_login_session_data(request, user)
        
        # If both methods are enabled, go to choice step
        if user.email_2fa_enabled and user.totp_enabled:
            return Response({
                'success': True,
                'message': '2FA required. Please choose your method.',
                'next_step': 'choose_2fa',
                'requires_2fa': True,
                'available_methods': ['email', 'totp']
            }, status=status.HTTP_200_OK)
        
        # If only email 2FA is enabled
        elif user.email_2fa_enabled:
            code = generate_email_code()
            user.email_2fa_code = code
            user.email_2fa_sent_at = timezone.now()
            user.save()
            
            # Initialize session data and set the chosen 2FA method
            session_data = initialize_login_session_data(request, user, code)
            session_data["chosen_2fa_method"] = "email"
            request.session["login_data"] = session_data
            
            success = send_2FA_email(user, code)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'A verification code has been sent to your email address.',
                    'next_step': 'email_2fa',
                    'requires_2fa': True,
                    'method': 'email'
                }, status=status.HTTP_200_OK)
            else:
                return AuthErrorResponse.server_error({
                    'email': 'Failed to send verification code'
                })
        
        # If only TOTP is enabled
        elif user.totp_enabled:
            # Initialize session data and set the chosen 2FA method
            session_data = initialize_login_session_data(request, user)
            session_data["chosen_2fa_method"] = "totp"
            request.session["login_data"] = session_data
            
            return Response({
                'success': True,
                'message': 'Please enter your TOTP code.',
                'next_step': 'totp_2fa',
                'requires_2FA': True,
                'method': 'totp'
            }, status=status.HTTP_200_OK)
    
    # No 2FA required, proceed to login
    return handle_login_success_api(request, user, remember_device)


def handle_login_step_2_2fa_choice_api(request):
    """Step 2: 2FA method choice"""
    serializer = TwoFAMethodChoiceSerializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return AuthErrorResponse.session_expired()
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.user_not_found("unknown")
    
    method = serializer.validated_data["chosen_method"]
    
    # Validate that the chosen 2FA method is enabled for this user
    if method == "email" and not user.email_2fa_enabled:
        return AuthErrorResponse.twofa_method_not_available("email")
    
    if method == "totp" and not user.totp_enabled:
        return AuthErrorResponse.twofa_method_not_available("totp")
    
    # Store the chosen method in session for the next step
    session_data["chosen_2fa_method"] = method
    request.session["login_data"] = session_data
    
    if method == "email":
        code = generate_email_code()
        user.email_2fa_code = code
        user.email_2fa_sent_at = timezone.now()
        user.save()
        
        session_data.update({
            "verification_code": code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        })
        request.session["login_data"] = session_data
        
        success = send_2FA_email(user, code)
        if success:
            return Response({
                'success': True,
                'message': 'Verification code sent to your email.',
                'next_step': 'email_2fa',
                'method': 'email'
            }, status=status.HTTP_200_OK)
        else:
            return AuthErrorResponse.server_error({
                'email': 'Failed to send verification code'
            })
    
    elif method == "totp":
        return Response({
            'success': True,
            'message': 'Please enter your TOTP code.',
            'next_step': 'totp_2fa',
            'method': 'totp'
        }, status=status.HTTP_200_OK)


def handle_login_step_3_email_2fa_api(request):
    """Step 3: Email 2FA verification"""
    serializer = Email2FASerializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return AuthErrorResponse.session_expired()
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.user_not_found("unknown")
    
    # Handle resend code request
    if serializer.validated_data.get("resend_code"):
        # Check if enough time has passed since last code
        code_sent_at = session_data.get("code_sent_at")
        if code_sent_at:
            sent_time = datetime.fromisoformat(
                code_sent_at.replace("Z", "+00:00")
                if code_sent_at.endswith("Z")
                else code_sent_at
            )
            if timezone.is_naive(sent_time):
                sent_time = timezone.make_aware(sent_time)
            
            time_since_sent = timezone.now() - sent_time
            if time_since_sent.total_seconds() < 60:  # 1 minute delay
                return AuthErrorResponse.too_many_attempts(0)
        
        # Generate and send new code
        new_code = generate_email_code()
        user.email_2fa_code = new_code
        user.email_2fa_sent_at = timezone.now()
        user.save()
        
        session_data.update({
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        })
        request.session["login_data"] = session_data
        
        success = send_2FA_email(user, new_code)
        if success:
            return Response({
                'success': True,
                'message': 'New verification code sent to your email.',
                'method': 'email'
            }, status=status.HTTP_200_OK)
        else:
            return AuthErrorResponse.server_error({
                'email': 'Failed to send verification code'
            })
    
    # Handle code verification
    submitted_code = serializer.validated_data.get("verification_code")
    if not submitted_code:
        return AuthErrorResponse.validation_error({
            'verification_code': ['Verification code is required']
        })
    
    stored_code = session_data.get("verification_code")
    code_sent_at = session_data.get("code_sent_at")
    attempts = session_data.get("code_attempts", 0)
    
    # Check attempt limit to prevent brute force attacks
    if attempts >= 3:
        return AuthErrorResponse.too_many_attempts(0)
    
    # Check code expiration (10 minutes from when code was sent)
    if code_sent_at:
        sent_time = datetime.fromisoformat(
            code_sent_at.replace("Z", "+00:00")
            if code_sent_at.endswith("Z")
            else code_sent_at
        )
        if timezone.is_naive(sent_time):
            sent_time = timezone.make_aware(sent_time)
        
        # Check if code has expired (10 minutes)
        if (timezone.now() - sent_time).total_seconds() > 600:  # 10 minutes
            return AuthErrorResponse.twofa_code_expired()
        
        # Validate the submitted code against stored code
        if submitted_code == stored_code:
            # Clear session data after successful verification
            request.session.pop("login_data", None)
            return handle_login_success_api(request, user, False)
        else:
            # Increment attempt counter and update session
            attempts += 1
            session_data["code_attempts"] = attempts
            request.session["login_data"] = session_data
            return AuthErrorResponse.invalid_2fa_code()
    
    return AuthErrorResponse.session_expired()


def handle_login_step_3_totp_2fa_api(request):
    """Step 3: TOTP 2FA verification"""
    serializer = TOTP2FASerializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return AuthErrorResponse.session_expired()
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.user_not_found("unknown")
    
    submitted_code = serializer.validated_data.get("totp_code")
    if not submitted_code:
        return AuthErrorResponse.validation_error({
            'totp_code': ['TOTP code is required']
        })
    
    # Check if user has TOTP enabled and has a valid secret
    if not user.totp_enabled or not user.twofa_totp_secret:
        return AuthErrorResponse.twofa_method_not_available("totp")
    
    # Verify TOTP code using user's secret key
    if verify_totp(user.twofa_totp_secret, submitted_code):
        # Clear session data after successful verification
        request.session.pop("login_data", None)
        return handle_login_success_api(request, user, False)
    else:
        return AuthErrorResponse.invalid_2fa_code()


def handle_login_success_api(request, user, remember_device):
    """Handle successful login completion"""
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_location_from_ip(ip)
    
    # Update login information
    user.is_online = True
    user.last_login_date = timezone.now()
    user.last_login_ip = ip
    user.save()
    
    # Handle trusted device creation if requested
    if remember_device:
        # Set session flag for trusted device
        request.session["remember_device"] = True
        
        # First, check if this device is already registered as trusted (by IP + User-Agent)
        from users.models import TrustedDevice
        existing_device = TrustedDevice.objects.filter(
            user=user,
            ip_address=ip,
            user_agent=user_agent[:255]
        ).first()
        
        if existing_device:
            # Device already exists - update it and don't create a new one
            existing_device.last_used_at = timezone.now()
            if location:
                existing_device.location = location
            existing_device.save(
                update_fields=["last_used_at", "location"]
            )
            
            # Check if we need to update the cookie
            trusted_tokens = [
                value
                for key, value in request.COOKIES.items()
                if key.startswith(f"trusted_device_{user.pk}")
            ]
            
            # If no valid cookie exists, create one for the existing device
            if not trusted_tokens:
                from users.utils import hash_token
                import uuid
                
                cookie_name = f"trusted_device_{user.pk}"
                max_age_days = 30
                max_age = max_age_days * 24 * 60 * 60
                
                # Generate new token for existing device
                token = f"{user.pk}-{uuid.uuid4().hex}"
                token_hash = hash_token(token)
                
                # Update device with new token
                existing_device.device_token = token_hash
                existing_device.expires_at = timezone.now() + timedelta(days=max_age_days)
                existing_device.save(update_fields=["device_token", "expires_at"])
                
                # Store token info for client
                request.session["trusted_device_token"] = token
                request.session["trusted_device_cookie_name"] = cookie_name
                request.session["trusted_device_max_age"] = max_age
        else:
            # Check for existing trusted device cookies (in case user has cookie but device was deleted from DB)
            trusted_tokens = [
                value
                for key, value in request.COOKIES.items()
                if key.startswith(f"trusted_device_{user.pk}")
            ]

            # Try to find an existing trusted device by token
            device = None
            for token in trusted_tokens:
                from users.utils import hash_token
                hashed_token = hash_token(token)
                device = TrustedDevice.objects.filter(
                    user=user, device_token=hashed_token
                ).first()
                if device:
                    break

            if device:
                # Update existing device with current usage information
                device.last_used_at = timezone.now()
                device.ip_address = ip
                device.user_agent = user_agent[:255]
                if location:
                    device.location = location
                device.save(
                    update_fields=["last_used_at", "ip_address", "user_agent", "location"]
                )
            else:
                # Create new trusted device
                from users.utils import hash_token
                from users.models import TrustedDevice
                
                cookie_name = f"trusted_device_{user.pk}"
                max_age_days = 30
                max_age = max_age_days * 24 * 60 * 60
                
                # Generate unique token
                token = f"{user.pk}-{uuid.uuid4().hex}"
                token_hash = hash_token(token)
                
                # Get device info from user agent
                from users.utils import _get_device_info_from_user_agent
                device_info = _get_device_info_from_user_agent(user_agent)
                
                # Create trusted device record
                TrustedDevice.objects.create(
                    user=user,
                    device_token=token_hash,
                    user_agent=user_agent[:255],
                    ip_address=ip,
                    location=location or "",
                    expires_at=timezone.now() + timedelta(days=max_age_days),
                    device_type=device_info.get("device_type", "Unknown Device"),
                    device_family=device_info.get("device_family", "Unknown"),
                    browser_family=device_info.get("browser_family", "Unknown"),
                    browser_version=device_info.get("browser_version", ""),
                    os_family=device_info.get("os_family", "Unknown"),
                    os_version=device_info.get("os_version", ""),
                )
                
                # Store token in session for client to set as cookie
                request.session["trusted_device_token"] = token
                request.session["trusted_device_cookie_name"] = cookie_name
                request.session["trusted_device_max_age"] = max_age
    
    # Log the connection
    log_user_action_json(
        user=user,
        action="login_api",
        request=request,
        ip_address=ip,
        extra_info={
            "remember_device": remember_device,
            "user_agent": user_agent[:200],
            "location": location,
        }
    )
    
    # Create JWT tokens
    tokens = create_tokens_for_user(user)
    user_data = UserSerializer(user).data
    
    response_data = {
        'success': True,
        'message': f'Welcome {user.first_name} !',
        'user': user_data,
        'tokens': tokens,
        'requires_2fa': False,
        'login_complete': True
    }
    
    # Add trusted device info if created
    if remember_device and "trusted_device_token" in request.session:
        response_data['trusted_device'] = {
            'token': request.session["trusted_device_token"],
            'cookie_name': request.session["trusted_device_cookie_name"],
            'max_age': request.session["trusted_device_max_age"],
            'expires_in_days': 30
        }
        # Clean up session data
        del request.session["trusted_device_token"]
        del request.session["trusted_device_cookie_name"]
        del request.session["trusted_device_max_age"]
    
    return Response(response_data, status=status.HTTP_200_OK)


# ===============================
# 2FA RESEND CODE API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_2fa_code_api(request):
    """Resend 2FA code for login"""
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return AuthErrorResponse.session_expired()
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return AuthErrorResponse.user_not_found("unknown")
    
    chosen_method = session_data.get("chosen_2fa_method")
    if not chosen_method:
        return AuthErrorResponse.validation_error({
            'method': ['No 2FA method selected']
        })
    
    # Check if enough time has passed since last code
    code_sent_at = session_data.get("code_sent_at")
    if code_sent_at:
        sent_time = datetime.fromisoformat(
            code_sent_at.replace("Z", "+00:00")
            if code_sent_at.endswith("Z")
            else code_sent_at
        )
        if timezone.is_naive(sent_time):
            sent_time = timezone.make_aware(sent_time)
        
        time_since_sent = timezone.now() - sent_time
        if time_since_sent.total_seconds() < 60:  # 1 minute delay
            remaining_time = int(60 - time_since_sent.total_seconds())
            return AuthErrorResponse.too_many_attempts(remaining_time)
    
    if chosen_method == "email":
        # Generate and send new email code
        new_code = generate_email_code()
        user.email_2fa_code = new_code
        user.email_2fa_sent_at = timezone.now()
        user.save()
        
        session_data.update({
            "verification_code": new_code,
            "code_sent_at": timezone.now().isoformat(),
            "code_attempts": 0,
        })
        request.session["login_data"] = session_data
        
        success = send_2FA_email(user, new_code)
        if success:
            return Response({
                'success': True,
                'message': 'New verification code sent to your email.',
                'method': 'email'
            }, status=status.HTTP_200_OK)
        else:
            return AuthErrorResponse.server_error({
                'email': 'Failed to send verification code'
            })
    
    elif chosen_method == "totp":
        return AuthErrorResponse.validation_error({
            'method': ['TOTP codes cannot be resent']
        })
    
    return AuthErrorResponse.validation_error({
        'method': ['Invalid 2FA method']
    })


# ===============================
# USER PROFILE API VIEWS
# ===============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication, SessionAuthentication])
def user_profile(request):
    """Get user profile information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication, SessionAuthentication])
def user_profile_full(request):
    """Get COMPLETE user profile information with all details"""
    user = request.user
    
    # Calculate age if date of birth is available
    age = None
    if user.date_of_birth:
        today = date.today()
        age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
    
    # Get user's photos statistics
    from photos.models import Photo
    user_photos = Photo.objects.filter(user=user)
    photo_stats = {
        'total_photos': user_photos.count(),
        'total_size_bytes': sum(photo.file_size for photo in user_photos),
        'total_size_mb': round(sum(photo.file_size for photo in user_photos) / (1024 * 1024), 2),
        'raw_photos': user_photos.filter(is_raw=True).count(),
        'jpeg_photos': user_photos.filter(file_extension__in=['jpg', 'jpeg']).count(),
        'recent_photos': user_photos.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
    }
    
    # Get user's collections
    from photos.models import Collection
    user_collections = Collection.objects.filter(owner=user)
    collection_stats = {
        'total_collections': user_collections.count(),
        'private_collections': user_collections.filter(is_private=True).count(),
        'public_collections': user_collections.filter(is_private=False).count(),
        'collections': [
            {
                'id': collection.id,
                'name': collection.name,
                'description': collection.description,
                'is_private': collection.is_private,
                'photo_count': collection.photos.count(),
                'created_at': collection.created_at,
            }
            for collection in user_collections
        ]
    }
    
    # Get trusted devices
    trusted_devices = user.trusted_devices.all()
    device_info = [
        {
            'device_token': device.device_token[:8] + '...',
            'device_type': device.device_type,
            'device_family': device.device_family,
            'browser_family': device.browser_family,
            'browser_version': device.browser_version,
            'os_family': device.os_family,
            'os_version': device.os_version,
            'ip_address': device.ip_address,
            'location': device.location,
            'created_at': device.created_at,
            'last_used_at': device.last_used_at,
            'expires_at': device.expires_at,
        }
        for device in trusted_devices
    ]
    
    # Comprehensive user data
    comprehensive_data = {
        "user_id": user.id,
        "basic_info": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "date_of_birth": user.date_of_birth,
            "age": age,
            "bio": user.bio,
            "is_private": user.is_private,
        },
        "profile_picture": {
            "url": request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
            "filename": user.profile_picture.name if user.profile_picture else None,
            "is_default": user.profile_picture.name == "profiles/default.jpg" if user.profile_picture else True,
        },
        "account_status": {
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_online": user.is_online,
            "is_anonymized": user.is_anonymized,
        },
        "verification_status": {
            "is_email_verified": user.is_email_verified,
            "email_verification_code": user.email_verification_code,
            "verification_code_sent_at": user.verification_code_sent_at,
            "can_send_verification_code": user.can_send_verification_code(),
        },
        "two_factor_auth": {
            "email_2fa_enabled": user.email_2fa_enabled,
            "email_2fa_code": user.email_2fa_code,
            "email_2fa_sent_at": user.email_2fa_sent_at,
            "totp_enabled": user.totp_enabled,
            "twofa_totp_secret": user.twofa_totp_secret[:8] + '...' if user.twofa_totp_secret else None,
        },
        "timestamps": {
            "date_joined": user.date_joined,
            "last_login_date": user.last_login_date,
            "last_login_ip": user.last_login_ip,
            "ip_address": user.ip_address,
        },
        "permissions": {
            "user_permissions": list(user.user_permissions.all().values_list('codename', flat=True)),
            "groups": list(user.groups.all().values_list('name', flat=True)),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
        "photo_statistics": photo_stats,
        "collection_statistics": collection_stats,
        "trusted_devices": {
            "count": trusted_devices.count(),
            "devices": device_info,
        },
        "api_endpoints": {
            "profile": request.build_absolute_uri("/api/v1/user/profile/"),
            "profile_full": request.build_absolute_uri("/api/v1/user/profile/full/"),
            "update_profile": request.build_absolute_uri("/api/v1/user/update/"),
            "photos": request.build_absolute_uri("/photos/api/photos/"),
            "collections": request.build_absolute_uri("/photos/api/collections/"),
            "stats": request.build_absolute_uri("/photos/api/stats/"),
        },
        "web_urls": {
            "profile_page": request.build_absolute_uri(f"/profile/"),
            "photos_page": request.build_absolute_uri("/photos/gallery/"),
            "collections_page": request.build_absolute_uri("/photos/collections/"),
            "settings_page": request.build_absolute_uri("/settings/dashboard/"),
        },
        "security_info": {
            "password_changed": user.password_changed if hasattr(user, 'password_changed') else None,
            "failed_login_attempts": getattr(user, 'failed_login_attempts', 0),
            "account_locked_until": getattr(user, 'account_locked_until', None),
        },
        "gdpr_compliance": {
            "is_anonymized": user.is_anonymized,
            "data_retention_policy": "User data is retained according to GDPR requirements",
            "right_to_be_forgotten": "Available through account anonymization",
            "data_portability": "Available through API endpoints",
        }
    }
    
    return Response(comprehensive_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    try:
        # Check if password is being changed
        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')
        
        if new_password and not current_password:
            return AuthErrorResponse.validation_error({
                'current_password': ['Current password is required when changing password']
            })
        
        if new_password and not request.user.check_password(current_password):
            return AuthErrorResponse.invalid_credentials()
        
        # Update password if provided
        if new_password:
            request.user.set_password(new_password)
        
        # Save other fields
        serializer.save()
        
        # Log the update
        ip = get_client_ip(request)
        log_user_action_json(
            user=request.user,
            action="profile_update_api",
            request=request,
            ip_address=ip,
            extra_info={"impacted_user_id": request.user.id}
        )
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully.',
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return AuthErrorResponse.server_error({
            'error': f'Error updating profile: {str(e)}'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """User logout"""
    user = request.user
    
    # Update status
    user.is_online = False
    user.save()
    
    # Log the logout
    ip = get_client_ip(request)
    log_user_action_json(
        user=user,
        action="logout_api",
        request=request,
        ip_address=ip,
        extra_info={"impacted_user_id": user.id}
    )
    
    return Response({
        'success': True,
        'message': 'Logout successful.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_session_api(request):
    """Refresh user session to keep it active"""
    user = request.user
    
    # Update online status
    user.is_online = True
    user.last_seen = timezone.now()
    user.save()
    
    # Log the session refresh
    ip = get_client_ip(request)
    log_user_action_json(
        user=user,
        action="session_refresh",
        request=request,
        ip_address=ip,
        extra_info={"impacted_user_id": user.id}
    )
    
    return Response({
        'success': True,
        'message': 'Session refreshed successfully.',
        'user_id': user.id,
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)


# ===============================
# UTILITY API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def check_username_availability(request):
    """
    API view to check username availability in real time.
    
    Returns JSON response with availability status and message.
    """
    serializer = RegisterStep4Serializer(data=request.data)
    
    if not serializer.is_valid():
        return AuthErrorResponse.validation_error(serializer.errors)
    
    username = serializer.validated_data['username']
    
    # Check availability (case-insensitive)
    is_available = not CustomUser.objects.filter(username=username, is_active=True).exists()
    
    if is_available:
        return Response({
            "available": True,
            "message": "Username is available",
            "username": username
        }, status=status.HTTP_200_OK)
    else:
        return AuthErrorResponse.username_already_taken(username)