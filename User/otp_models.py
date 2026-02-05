"""
Email OTP Model
Handles OTP storage with security features
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string


class EmailOTP(models.Model):
    """
    Stores OTP codes for email verification
    Features:
    - 6-digit OTP
    - 5-minute expiry
    - Max 3 verification attempts
    - Rate limiting (max 3 OTPs per hour per email)
    """
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Login'),
            ('signup', 'Signup'),
            ('address_verification', 'Address Verification'),
            ('password_reset', 'Password Reset'),
        ],
        default='login'
    )
    
    # Security tracking
    attempts = models.IntegerField(default=0, help_text="Number of verification attempts")
    max_attempts = models.IntegerField(default=3)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # User reference (optional - for logged-in users)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='email_otps')
    
    class Meta:
        db_table = 'email_otps'
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'purpose', 'created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.email} ({self.purpose}) - {'Verified' if self.is_verified else 'Pending'}"
    
    def save(self, *args, **kwargs):
        # Set expiry time if not set (5 minutes from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if OTP is still valid (not expired, not used, attempts remaining)"""
        return (
            not self.is_expired and 
            not self.is_used and 
            self.attempts < self.max_attempts
        )
    
    @property
    def attempts_remaining(self):
        """Get remaining verification attempts"""
        return max(0, self.max_attempts - self.attempts)
    
    @property
    def time_remaining_seconds(self):
        """Get remaining time in seconds before expiry"""
        if self.is_expired:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))
    
    def increment_attempts(self):
        """Increment attempt counter"""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        return self.attempts
    
    def mark_verified(self):
        """Mark OTP as verified"""
        self.is_verified = True
        self.is_used = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'is_used', 'verified_at'])
    
    def mark_used(self):
        """Mark OTP as used (without verification - for invalidation)"""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, email, purpose='login', user=None, expiry_minutes=5):
        """
        Create a new OTP for an email
        Invalidates any previous unused OTPs for this email/purpose
        """
        # Invalidate previous OTPs for this email and purpose
        cls.objects.filter(
            email=email.lower(),
            purpose=purpose,
            is_used=False
        ).update(is_used=True)
        
        # Create new OTP
        otp = cls.objects.create(
            email=email.lower(),
            otp_code=cls.generate_otp(),
            purpose=purpose,
            user=user,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
        )
        return otp
    
    @classmethod
    def get_rate_limit_count(cls, email, purpose, hours=1):
        """
        Get the number of OTPs sent to this email in the last X hours
        Used for rate limiting
        """
        cutoff = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(
            email=email.lower(),
            purpose=purpose,
            created_at__gte=cutoff
        ).count()
    
    @classmethod
    def can_send_otp(cls, email, purpose, max_per_hour=5):
        """
        Check if we can send another OTP (rate limiting)
        Returns tuple: (can_send, wait_seconds)
        """
        count = cls.get_rate_limit_count(email, purpose)
        if count >= max_per_hour:
            # Find the oldest OTP in the last hour
            cutoff = timezone.now() - timedelta(hours=1)
            oldest = cls.objects.filter(
                email=email.lower(),
                purpose=purpose,
                created_at__gte=cutoff
            ).order_by('created_at').first()
            
            if oldest:
                wait_until = oldest.created_at + timedelta(hours=1)
                wait_seconds = max(0, int((wait_until - timezone.now()).total_seconds()))
                return False, wait_seconds
            return False, 3600  # Default 1 hour wait
        
        return True, 0
    
    @classmethod
    def get_resend_wait_time(cls, email, purpose, min_interval_seconds=60):
        """
        Get remaining wait time before resend is allowed
        Returns seconds to wait (0 if can resend now)
        """
        latest = cls.objects.filter(
            email=email.lower(),
            purpose=purpose,
            is_used=False
        ).order_by('-created_at').first()
        
        if not latest:
            return 0
        
        elapsed = (timezone.now() - latest.created_at).total_seconds()
        if elapsed < min_interval_seconds:
            return int(min_interval_seconds - elapsed)
        return 0
    
    @classmethod
    def verify_otp(cls, email, otp_code, purpose):
        """
        Verify an OTP code
        Returns tuple: (success, message, otp_object)
        """
        otp = cls.objects.filter(
            email=email.lower(),
            purpose=purpose,
            is_used=False
        ).order_by('-created_at').first()
        
        if not otp:
            return False, 'No active OTP found. Please request a new one.', None
        
        if otp.is_expired:
            otp.mark_used()
            return False, 'OTP has expired. Please request a new one.', otp
        
        if otp.attempts >= otp.max_attempts:
            otp.mark_used()
            return False, 'Maximum attempts exceeded. Please request a new OTP.', otp
        
        # Increment attempts
        otp.increment_attempts()
        
        if otp.otp_code != otp_code:
            remaining = otp.attempts_remaining
            if remaining == 0:
                otp.mark_used()
                return False, 'Invalid OTP. Maximum attempts exceeded.', otp
            return False, f'Invalid OTP. {remaining} attempts remaining.', otp
        
        # Success!
        otp.mark_verified()
        return True, 'OTP verified successfully.', otp
