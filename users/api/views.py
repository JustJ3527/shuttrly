# Standard library imports
from datetime import datetime
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
    get_client_ip, get_user_agent, get_location_from_ip
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
    """User login"""
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        remember_device = serializer.validated_data.get('remember_device', False)
        
        # Update login information
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        location = get_location_from_ip(ip)
        
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
            'requires_2fa': user.email_2fa_enabled or user.totp_enabled
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Incorrect credentials.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# USER PROFILE API VIEWS
# ===============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Recover user profile"""
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)


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