"""
Email OTP Authentication Views
Handles OTP generation, verification, and resending with security measures
"""
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken


# OTP Settings (with defaults)
OTP_EXPIRY_MINUTES = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
OTP_MAX_ATTEMPTS = getattr(settings, 'OTP_MAX_ATTEMPTS', 3)
OTP_RATE_LIMIT_PER_HOUR = getattr(settings, 'OTP_RATE_LIMIT_PER_HOUR', 5)
OTP_RESEND_INTERVAL_SECONDS = getattr(settings, 'OTP_RESEND_INTERVAL_SECONDS', 60)


def generate_otp():
    """Generate a cryptographically secure 6-digit OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def hash_otp(otp: str) -> str:
    """Hash OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()


def get_cache_key(email: str, purpose: str, key_type: str) -> str:
    """Generate cache key for OTP storage"""
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"otp:{purpose}:{email_hash}:{key_type}"


def get_rate_limit_key(email: str) -> str:
    """Generate rate limit cache key"""
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"otp_rate:{email_hash}"


class SendEmailOTPAPIView(APIView):
    """
    Send OTP to user's email address
    
    POST /user/auth/otp/send/
    {
        "email": "user@example.com",
        "purpose": "login" | "signup" | "address_verification"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        purpose = request.data.get('purpose', 'login')
        
        # Validate email
        if not email or '@' not in email:
            return Response(
                {'error': 'Valid email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate purpose
        valid_purposes = ['login', 'signup', 'address_verification']
        if purpose not in valid_purposes:
            return Response(
                {'error': f'Invalid purpose. Must be one of: {", ".join(valid_purposes)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check rate limiting
        rate_key = get_rate_limit_key(email)
        request_count = cache.get(rate_key, 0)
        
        if request_count >= OTP_RATE_LIMIT_PER_HOUR:
            return Response(
                {
                    'error': 'Too many OTP requests. Please try again later.',
                    'retry_after_seconds': 3600
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Check resend interval
        last_sent_key = get_cache_key(email, purpose, 'last_sent')
        last_sent = cache.get(last_sent_key)
        
        if last_sent:
            elapsed = (timezone.now() - last_sent).total_seconds()
            remaining = OTP_RESEND_INTERVAL_SECONDS - elapsed
            
            if remaining > 0:
                return Response(
                    {
                        'error': 'Please wait before requesting a new code',
                        'resend_after_seconds': int(remaining)
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        # For login, check if user exists
        if purpose == 'login':
            if not User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'No account found with this email. Please sign up first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Generate OTP
        otp = generate_otp()
        otp_hash = hash_otp(otp)
        
        # Store OTP data
        otp_key = get_cache_key(email, purpose, 'otp')
        attempts_key = get_cache_key(email, purpose, 'attempts')
        expiry_seconds = OTP_EXPIRY_MINUTES * 60
        
        cache.set(otp_key, otp_hash, expiry_seconds)
        cache.set(attempts_key, 0, expiry_seconds)
        cache.set(last_sent_key, timezone.now(), OTP_RESEND_INTERVAL_SECONDS)
        
        # Increment rate limit counter
        cache.set(rate_key, request_count + 1, 3600)  # 1 hour TTL
        
        # Send email
        subject = self._get_email_subject(purpose)
        plain_message = self._get_email_message(otp, purpose)
        html_message = self._render_html_email(otp, purpose)

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            if html_message:
                msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
        except Exception as e:
            print(f"❌ Failed to send OTP email: {e}")
            # In development, print OTP to console
            if settings.DEBUG:
                print(f"🔐 OTP for {email}: {otp}")
            else:
                return Response(
                    {'error': 'Failed to send verification email. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({
            'success': True,
            'message': 'Verification code sent to your email',
            'expires_in_seconds': expiry_seconds,
            'resend_after_seconds': OTP_RESEND_INTERVAL_SECONDS
        })
    
    def _get_email_subject(self, purpose: str) -> str:
        subjects = {
            'login': 'Your Raggey Login Code',
            'signup': 'Welcome to Raggey - Verify Your Email',
            'address_verification': 'Raggey - Confirm Your Email Address'
        }
        return subjects.get(purpose, 'Your Raggey Verification Code')
    
    def _get_email_message(self, otp: str, purpose: str) -> str:
        messages = {
            'login': f"""
Hello,

Your login verification code is: {otp}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
The Raggey Team
            """,
            'signup': f"""
Welcome to Raggey!

Your verification code is: {otp}

Enter this code to complete your registration.
This code will expire in {OTP_EXPIRY_MINUTES} minutes.

Best regards,
The Raggey Team
            """,
            'address_verification': f"""
Hello,

You're adding a new delivery address to your Raggey account.

Your verification code is: {otp}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this, please ignore this email.

Best regards,
The Raggey Team
            """
        }
        return messages.get(purpose, f"Your verification code is: {otp}")

    def _render_html_email(self, otp: str, purpose: str) -> str:
        """Render HTML email template for OTP"""
        template_map = {
            'login': 'emails/otp_login.html',
            'signup': 'emails/otp_signup.html',
        }
        template_name = template_map.get(purpose)
        if not template_name:
            return None

        from datetime import datetime
        context = {
            'otp_code': otp,
            'otp_1': otp[0],
            'otp_2': otp[1],
            'otp_3': otp[2],
            'otp_4': otp[3],
            'otp_5': otp[4],
            'otp_6': otp[5],
            'expiry_minutes': OTP_EXPIRY_MINUTES,
            'current_year': datetime.now().year,
        }
        try:
            return render_to_string(template_name, context)
        except Exception as e:
            print(f"⚠️ Failed to render HTML email template: {e}")
            return None


class VerifyEmailOTPAPIView(APIView):
    """
    Verify OTP code
    
    POST /user/auth/otp/verify/
    {
        "email": "user@example.com",
        "otp": "123456",
        "purpose": "login" | "signup" | "address_verification",
        "full_name": "John Doe",  // for signup only
        "phone_number": "+96512345678"  // for signup only
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        otp = request.data.get('otp', '').strip()
        purpose = request.data.get('purpose', 'login')
        
        # Validate inputs
        if not email or '@' not in email:
            return Response(
                {'error': 'Valid email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not otp or len(otp) != 6 or not otp.isdigit():
            return Response(
                {'error': 'Invalid OTP format. Must be 6 digits.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get stored OTP data
        otp_key = get_cache_key(email, purpose, 'otp')
        attempts_key = get_cache_key(email, purpose, 'attempts')
        
        stored_otp_hash = cache.get(otp_key)
        attempts = cache.get(attempts_key, 0)
        
        # Check if OTP exists
        if not stored_otp_hash:
            return Response(
                {'error': 'OTP expired or not found. Please request a new code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempts
        if attempts >= OTP_MAX_ATTEMPTS:
            # Clear OTP after max attempts
            cache.delete(otp_key)
            cache.delete(attempts_key)
            return Response(
                {'error': 'Too many failed attempts. Please request a new code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify OTP
        provided_otp_hash = hash_otp(otp)
        
        if provided_otp_hash != stored_otp_hash:
            # Increment attempts
            remaining_attempts = OTP_MAX_ATTEMPTS - attempts - 1
            cache.set(attempts_key, attempts + 1, OTP_EXPIRY_MINUTES * 60)
            
            return Response(
                {
                    'error': 'Invalid verification code',
                    'attempts_remaining': remaining_attempts
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP is valid - clear from cache
        cache.delete(otp_key)
        cache.delete(attempts_key)
        
        # Handle different purposes
        if purpose == 'login':
            return self._handle_login(email)
        elif purpose == 'signup':
            return self._handle_signup(email, request.data)
        elif purpose == 'address_verification':
            return self._handle_address_verification(email)
        else:
            return Response({
                'success': True,
                'verified': True,
                'message': 'Email verified successfully'
            })
    
    def _handle_login(self, email: str) -> Response:
        """Handle login after OTP verification"""
        try:
            user = User.objects.get(email=email)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'verified': True,
                'message': 'Login successful',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.get_full_name() or user.username,
                }
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _handle_signup(self, email: str, data: dict) -> Response:
        """Handle signup after OTP verification"""
        full_name = data.get('full_name', '')
        phone_number = data.get('phone_number', '')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            # User exists - just log them in
            return self._handle_login(email)
        
        # Create new user
        username = email.split('@')[0]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Parse full name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        
        # Save phone number to profile if exists
        try:
            from .models import UserData
            UserData.objects.update_or_create(
                user=user,
                defaults={'phone_number': phone_number}
            )
        except Exception:
            pass  # Profile model might not exist
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'verified': True,
            'message': 'Account created successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.get_full_name() or user.username,
            }
        }, status=status.HTTP_201_CREATED)
    
    def _handle_address_verification(self, email: str) -> Response:
        """Handle address email verification"""
        return Response({
            'success': True,
            'verified': True,
            'message': 'Email verified successfully'
        })


class ResendEmailOTPAPIView(APIView):
    """
    Resend OTP to user's email
    
    POST /user/auth/otp/resend/
    {
        "email": "user@example.com",
        "purpose": "login" | "signup" | "address_verification"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # This is essentially the same as SendEmailOTPAPIView
        # Delegate to the send view
        send_view = SendEmailOTPAPIView()
        return send_view.post(request)


class CheckOTPStatusAPIView(APIView):
    """
    Check OTP status for an email
    
    GET /user/auth/otp/status/?email=user@example.com&purpose=login
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        email = request.query_params.get('email', '').lower().strip()
        purpose = request.query_params.get('purpose', 'login')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        otp_key = get_cache_key(email, purpose, 'otp')
        attempts_key = get_cache_key(email, purpose, 'attempts')
        last_sent_key = get_cache_key(email, purpose, 'last_sent')
        
        has_active_otp = cache.get(otp_key) is not None
        attempts = cache.get(attempts_key, 0)
        last_sent = cache.get(last_sent_key)
        
        # Calculate time until can resend
        can_resend = True
        resend_after_seconds = 0
        
        if last_sent:
            elapsed = (timezone.now() - last_sent).total_seconds()
            remaining = OTP_RESEND_INTERVAL_SECONDS - elapsed
            
            if remaining > 0:
                can_resend = False
                resend_after_seconds = int(remaining)
        
        return Response({
            'has_active_otp': has_active_otp,
            'attempts_used': attempts,
            'attempts_remaining': OTP_MAX_ATTEMPTS - attempts,
            'can_resend': can_resend,
            'resend_after_seconds': resend_after_seconds
        })
