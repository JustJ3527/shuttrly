# Standard library imports
from datetime import datetime, date, timedelta
import uuid

# Third party imports
from django.core.files import temp
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from users.models import CustomUser
from users.validators import UsernameValidator
from users.utils import (
    generate_email_code, send_verification_email,
    get_client_ip, get_user_agent, get_location_from_ip,
    send_2FA_email, verify_totp, is_trusted_device,
    initialize_login_session_data
)
from users.constants import EMAIL_CODE_RESEND_DELAY_SECONDS, EMAIL_CODE_EXPIRY_SECONDS
from logs.utils import log_user_action_json

from users.api.serializers import (
    RegisterStep1Serializer, RegisterStep2Serializer, RegisterStep3Serializer,
    RegisterStep4Serializer, RegisterStep5Serializer, LoginSerializer, ResendCodeSerializer, UserSerializer,
    create_tokens_for_user
)

# ===============================
# REGISTRATION API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_step_1_email(request):
    """Step 1: Email verification and sending code"""
    serializer = RegisterStep1Serializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']

        # Clean temporary users
        CustomUser.objects.filter(email=email, is_active=False).delete()

        # Generate verification code
        verification_code = generate_email_code()


        # Create temporary user
        temp_username = f"temp_{uuid.uuid4().hex[:8]}"
        while CustomUser.objects.filter(username=temp_username).exists():
            temp_username = f"temp_{uuid.uuid4().hex[:8]}"

        temp_user = CustomUser.objects.create(
            email=email,
            username=temp_username,
            first_name="",
            last_name="",
            is_active=False,
            email_verification_code=verification_code,
            verification_code_sent_at=timezone.now()
        )

        # Send email
        success = send_verification_email(email, verification_code)

        if success:
            return Response({
                'success': True,
                "message": f"Verification code sent to your mail: {email}",
                'email': email,
                'temp_user_id': temp_user.id
            }, status=status.HTTP_200_OK)
        else:
            temp_user.delete()
            return Response({
                'success': False,
                "message": "Failed to send verification code",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_step_2_verifify_email(request):
    """Step 2: Verify email"""
    serializer = RegisterStep2Serializer(data=request.data)
    
    if serializer.is_valid():
        email = request.data.get("email")
        submitted_code = serializer.validated_data["verification_code"]

        try:
            temp_user = CustomUser.objects.get(email=email, is_active=False)

            # Check code expiration
            if temp_user.verification_code_sent_at:
                time_since_sent = timezone.now() - temp_user.verification_code_sent_at
                if time_since_sent.total_seconds() > EMAIL_CODE_EXPIRY_SECONDS:
                    return Response({
                        'success': False,
                        "message": "Verification code has expired",
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Check code
            if temp_user.email_verification_code == submitted_code:
                temp_user.delete() #Clean temporary user

                return Response({
                    "success": True, 
                    "message": "Email verification successful",
                    "email_verified": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "message": "Incorrect code."
                }, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response({
                "success": False,
                "message": "Session expired. Please try registration again."
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_complete(request):
    """Complete registration with all required information"""
    # Verify that all required information is present
    required_fields = ['email', 'first_name', 'last_name', 'date_of_birth', 'username', 'password1', 'password2']
    for field in required_fields:
        if not request.data.get(field):
            return Response({
                'success': False,
                'message': f'The field {field} is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate each step
    step1_data = {'email': request.data['email']}
    step1_serializer = RegisterStep1Serializer(data=step1_data)
    if not step1_serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid email.',
            'errors': step1_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    step3_data = {
        'first_name': request.data['first_name'],
        'last_name': request.data['last_name'],
        'date_of_birth': request.data['date_of_birth']
    }
    step3_serializer = RegisterStep3Serializer(data=step3_data)
    if not step3_serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid personal information.',
            'errors': step3_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    step4_data = {'username': request.data['username']}
    step4_serializer = RegisterStep4Serializer(data=step4_data)
    if not step4_serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invlaid username.',
            'errors': step4_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    step5_data = {
        'password1': request.data['password1'],
        'password2': request.data['password2']
    }
    step5_serializer = RegisterStep5Serializer(data=step5_data)
    if not step5_serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid passwords.',
            'errors': step5_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user
    try:
        user = CustomUser.objects.create_user(
            email=request.data['email'],
            username=request.data['username'].lower(),
            password=request.data['password1'],
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
            date_of_birth=datetime.strptime(request.data['date_of_birth'], '%Y-%m-%d').date(),
            is_email_verified=True,  # Email already verified at step 2
        )
        
        # Log account creation
        ip = get_client_ip(request)
        user.ip_address = ip
        user.save()
        
        log_user_action_json(
            user=user,
            action="register_api",
            request=request,
            ip_address=ip,
            extra_info={"impacted_user_id": user.id}
        )
        
        # Create JWT tokens
        tokens = create_tokens_for_user(user)
        user_data = UserSerializer(user).data
        
        return Response({
            'success': True,
            'message': 'Account created successfully!',
            'user': user_data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error creating account: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    """Resend a verification code"""
    serializer = ResendCodeSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            temp_user = CustomUser.objects.get(email=email, is_active=False)
            
            # Check the time between shipments
            if temp_user.verification_code_sent_at:
                time_since_sent = timezone.now() - temp_user.verification_code_sent_at
                if time_since_sent.total_seconds() < EMAIL_CODE_RESEND_DELAY_SECONDS:
                    remaining_time = int(EMAIL_CODE_RESEND_DELAY_SECONDS - time_since_sent.total_seconds())
                    return Response({
                        'success': False,
                        'message': f'Please wait {remaining_time} seconds before requesting a new code.'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Generate and send a new code
            new_code = generate_email_code()
            temp_user.email_verification_code = new_code
            temp_user.verification_code_sent_at = timezone.now()
            temp_user.save()
            
            success = send_verification_email(email, new_code)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'New code sent successdully.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Error sending code.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No current registration found for this email.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# LOGIN API VIEWS
# ===============================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """User login with 2FA support"""
    step = request.data.get('step', 'credentials')
    
    if step == 'credentials':
        return handle_login_step_1_credentials_api(request)
    elif step == 'choose_2fa':
        return handle_login_step_2_2fa_choice_api(request)
    elif step == 'email_2fa':
        return handle_login_step_3_email_2fa_api(request)
    elif step == 'totp_2fa':
        return handle_login_step_3_totp_2fa_api(request)
    else:
        return Response({
            'success': False,
            'message': 'Invalid step.',
            'errors': {'step': 'Invalid step parameter'}
        }, status=status.HTTP_400_BAD_REQUEST)


def handle_login_step_1_credentials_api(request):
    """Step 1: Credentials validation"""
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        remember_device = serializer.validated_data.get('remember_device', False)
        
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
                    return Response({
                        'success': False,
                        'message': 'Error sending verification code.',
                        'errors': {'email': 'Failed to send verification code'}
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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
                    'requires_2fa': True,
                    'method': 'totp'
                }, status=status.HTTP_200_OK)
        
        # No 2FA required, proceed to login
        return handle_login_success_api(request, user, remember_device)
    
    return Response({
        'success': False,
        'message': 'Incorrect credentials.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


def handle_login_step_2_2fa_choice_api(request):
    """Step 2: 2FA method choice"""
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return Response({
            'success': False,
            'message': 'Session expired. Please try again.',
            'errors': {'session': 'Session expired'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found.',
            'errors': {'user': 'User not found'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    method = request.data.get("twofa_method")
    
    if not method or method not in ['email', 'totp']:
        return Response({
            'success': False,
            'message': 'Invalid 2FA method selection.',
            'errors': {'twofa_method': 'Invalid method'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate that the chosen 2FA method is enabled for this user
    if method == "email" and not user.email_2fa_enabled:
        return Response({
            'success': False,
            'message': 'Email 2FA is not enabled for this account.',
            'errors': {'twofa_method': 'Email 2FA not enabled'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if method == "totp" and not user.totp_enabled:
        return Response({
            'success': False,
            'message': 'TOTP 2FA is not enabled for this account.',
            'errors': {'twofa_method': 'TOTP 2FA not enabled'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
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
            return Response({
                'success': False,
                'message': 'Error sending verification code.',
                'errors': {'email': 'Failed to send code'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif method == "totp":
        return Response({
            'success': True,
            'message': 'Please enter your TOTP code.',
            'next_step': 'totp_2fa',
            'method': 'totp'
        }, status=status.HTTP_200_OK)


def handle_login_step_3_email_2fa_api(request):
    """Step 3: Email 2FA verification"""
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return Response({
            'success': False,
            'message': 'Session expired. Please try again.',
            'errors': {'session': 'Session expired'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found.',
            'errors': {'user': 'User not found'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle resend code request
    if request.data.get("resend_code"):
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
                return Response({
                    'success': False,
                    'message': 'Please wait before requesting a new code.',
                    'errors': {'resend': 'Too soon to resend'}
                }, status=status.HTTP_400_BAD_REQUEST)
        
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
            return Response({
                'success': False,
                'message': 'Error sending verification code.',
                'errors': {'email': 'Failed to send code'}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Handle code verification
    submitted_code = request.data.get("twofa_code")
    if not submitted_code:
        return Response({
            'success': False,
            'message': 'Verification code is required.',
            'errors': {'twofa_code': 'Code required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    stored_code = session_data.get("verification_code")
    code_sent_at = session_data.get("code_sent_at")
    attempts = session_data.get("code_attempts", 0)
    
    # Check attempt limit to prevent brute force attacks
    if attempts >= 3:
        return Response({
            'success': False,
            'message': 'Too many attempts. Request a new code.',
            'errors': {'twofa_code': 'Too many attempts'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
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
            return Response({
                'success': False,
                'message': 'Code has expired. Request a new code.',
                'errors': {'twofa_code': 'Code expired'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            return Response({
                'success': False,
                'message': f'Incorrect code. {3-attempts} remaining attempt(s).',
                'errors': {'twofa_code': f'Incorrect code. {3-attempts} attempts remaining'}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'message': 'Session error. Please try again.',
        'errors': {'session': 'Session error'}
    }, status=status.HTTP_400_BAD_REQUEST)


def handle_login_step_3_totp_2fa_api(request):
    """Step 3: TOTP 2FA verification"""
    session_data = request.session.get("login_data", {})
    user_id = session_data.get("user_id")
    
    if not user_id:
        return Response({
            'success': False,
            'message': 'Session expired. Please try again.',
            'errors': {'session': 'Session expired'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found.',
            'errors': {'user': 'User not found'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    submitted_code = request.data.get("twofa_code")
    if not submitted_code:
        return Response({
            'success': False,
            'message': 'TOTP code is required.',
            'errors': {'twofa_code': 'Code required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user has TOTP enabled and has a valid secret
    if not user.totp_enabled or not user.twofa_totp_secret:
        return Response({
            'success': False,
            'message': 'TOTP 2FA is not enabled for this account.',
            'errors': {'twofa_code': 'TOTP not enabled'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify TOTP code using user's secret key
    if verify_totp(user.twofa_totp_secret, submitted_code):
        # Clear session data after successful verification
        request.session.pop("login_data", None)
        return handle_login_success_api(request, user, False)
    else:
        return Response({
            'success': False,
            'message': 'Invalid TOTP code.',
            'errors': {'twofa_code': 'Invalid code'}
        }, status=status.HTTP_400_BAD_REQUEST)


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
    
    return Response({
        'success': True,
        'message': f'Welcome {user.first_name} !',
        'user': user_data,
        'tokens': tokens,
        'requires_2fa': False,
        'login_complete': True
    }, status=status.HTTP_200_OK)


# ===============================
# USER PROFILE API VIEWS
# ===============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get user profile information"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    """Mettre à jour le profil utilisateur"""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
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
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Invalid data.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


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
    username = request.data.get("username", "").strip()
    validator = UsernameValidator()

    if not username:
        return Response({
            "available": False, 
            "message": "Username required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use the same validator as the forms (converts to lowercase)
        validator.validate(username)
    except ValidationError as e:
        return Response({
            "available": False, 
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check availability (case-insensitive)
    # The validator already converted username to lowercase
    is_available = not CustomUser.objects.filter(username__iexact=username).exists()

    return Response({
        "available": is_available,
        "message": "Available" if is_available else "Already taken",
    }, status=status.HTTP_200_OK)