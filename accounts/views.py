from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import random
from .models import User
from gigs.models import Gig
from .utils import send_verification

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    try:
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        name = request.data.get('name')

        if not phone_number or not password or not name:
            return Response({"success": False, "error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()
        
        if user:
            if user.is_verified:
                return Response({"success": False, "error": "User already exists and is verified. Please login."}, status=status.HTTP_400_BAD_REQUEST)

            verification_code = str(random.randint(100000, 999999))
            user.verification_code = verification_code
            user.verification_expires = now() + timedelta(minutes=10)
            user.save()
            
            send_verification(phone_number, verification_code)
            
            return Response({"success": True, "message": "Verification code resent. Please verify your phone number."})

        verification_code = str(random.randint(100000, 999999))
        user = User.objects.create_user(phone_number=phone_number, password=password, name=name)
        user.verification_code = verification_code
        user.verification_expires = now() + timedelta(minutes=10)
        user.save()

        send_verification(phone_number, verification_code)
        return Response({"success": True, "message": "Please verify your phone number."}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_phone(request):
    try:
        phone_number = request.data.get('phone_number')
        verification_code = request.data.get('verification_code')

        user = User.objects.filter(phone_number=phone_number, verification_code=verification_code, verification_expires__gt=now()).first()

        if not user:
            return Response({"success": False, "error": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.verification_code = None
        user.verification_expires = None
        user.save()
        
        refresh = RefreshToken.for_user(user)  
        token = str(refresh.access_token)  

        return Response({"success": True, "message": "Phone number verified successfully.", "token": token})

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    try:
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response({"success": False, "error": "No account found with this phone number. Please sign up."}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({"success": False, "error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({"success": False, "error": "Phone number not verified. Signup again."}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)  
        token = str(refresh.access_token)  

        return Response({"success": True, "token": token, "user": {"id": user.id, "name": user.name, "phone_number": user.phone_number}})

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    try:
        phone_number = request.data.get('phone_number')

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response({"success": False, "error": "No account found with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"success": False, "error": "Phone number is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        verification_code = str(random.randint(100000, 999999))
        user.verification_code = verification_code
        user.verification_expires = now() + timedelta(minutes=10)
        user.save()

        send_verification(phone_number, verification_code)
        return Response({"success": True, "message": "Verification code resent successfully."})

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    try:
        phone_number = request.data.get('phone_number')

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response({"success": False, "error": "No account found with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        reset_code = str(random.randint(100000, 999999))
        reset_code_expires = now() + timedelta(minutes=10)

        user.reset_code = reset_code
        user.reset_code_expires = reset_code_expires
        user.save()

        send_verification(phone_number, reset_code)

        return Response({"success": True, "message": "Password reset code sent to your phone number."})

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    try:
        phone_number = request.data.get('phone_number')
        reset_code = request.data.get('reset_code')
        new_password = request.data.get('new_password')
        
        if not phone_number or not reset_code or not new_password:
            return Response({"success": False, "error": "Phone number, reset code, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response({"success": False, "error": "No account found with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        if user.reset_code != reset_code:
            return Response({"success": False, "error": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.reset_code = None  
        user.reset_code_expires = None  
        user.save()

        return Response({"success": True, "message": "Password reset successfully."})

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_info(request):
    try:
        token = request.headers.get('Authorization')
        
        if not token:
            return Response({"success": False, "error": "No token provided."}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = User.objects.filter(id=request.user.id).first()

        if not user:
            return Response({"success": False, "error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        gigs = Gig.objects.filter(creator=user, is_unlisted=False)
        
        gigs_data = [
            {
                "id": gig.id,
                "title": gig.title,
                "description": gig.description,
                "price": str(gig.price),
                "category": gig.category,
                "location": gig.location,
                "number_of_raters": gig.number_of_raters,
                "rating": gig.rating,
                "created_at": gig.created_at,
                "updated_at": gig.updated_at,
            }
            for gig in gigs
        ]

        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "phone_number": user.phone_number,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
            },
            "gigs": gigs_data
        })

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
