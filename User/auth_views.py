"""
Authentication Views
Handles user signup, login, and logout with JWT tokens
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import UserSignupSerializer, UserLoginSerializer


class UserSignupAPIView(APIView):
    """
    POST: Register a new user
    Endpoint: /user/auth/signup/
    """
    permission_classes = []  # Public endpoint

    def post(self, request):
        try:
            serializer = UserSignupSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Extract data
            username = serializer.validated_data['username'].lower()
            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']
            full_name = serializer.validated_data.get('full_name', '')
            phone_number = serializer.validated_data.get('phone_number', '')

            # Check if user exists
            if User.objects.filter(email=email).exists():
                return Response({
                    'error': 'Email already registered'
                }, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(username=username).exists():
                return Response({
                    'error': 'Username already taken'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Split full name into first/last
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0] if name_parts else ''
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.save()

            # Create or update user profile with phone number
            from .models import Profile
            profile, created = Profile.objects.get_or_create(user=user)
            if phone_number:
                profile.phone_number = phone_number
                profile.save()

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'message': 'User registered successfully',
                'access': access_token,
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': full_name,
                    'phone_number': phone_number,
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Signup failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLoginAPIView(APIView):
    """
    POST: Login existing user
    Endpoint: /user/auth/login/
    """
    permission_classes = []  # Public endpoint

    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']

            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials',
                    'message': 'Email not registered'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check password
            if not user.check_password(password):
                return Response({
                    'error': 'Invalid credentials',
                    'message': 'Incorrect password'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Get user profile
            from .models import Profile
            profile = Profile.objects.filter(user=user).first()
            phone_number = profile.phone_number if profile else ''

            # Remove from force logout table (if present)
            from .force_logout_model import ForceLogoutUser
            ForceLogoutUser.remove_user(user)

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'message': 'Login successful',
                'access': access_token,
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': f'{user.first_name} {user.last_name}'.strip(),
                    'phone_number': phone_number,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Login failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogoutAPIView(APIView):
    """
    POST: Logout user
    Endpoint: /user/auth/logout/
    Clears FCM token from backend
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get user profile
            from .models import Profile
            profile = Profile.objects.filter(user=request.user).first()
            
            if profile:
                # Clear FCM token
                profile.fcm_token = ''
                profile.save()
                
                print(f'✅ Logout: FCM token cleared for user {request.user.email}')
                
                return Response({
                    'success': True,
                    'message': 'Logged out successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'User profile not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            print(f'❌ Logout error: {e}')
            return Response({
                'success': False,
                'error': 'Logout failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
