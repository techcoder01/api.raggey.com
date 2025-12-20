from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Coupon(models.Model):
    """
    Coupon model for promo codes
    Supports both input codes and card-style promotional coupons
    """
    COUPON_TYPE_CHOICES = [
        ('beta', 'Beta Code'),
        ('card', 'Card Promo'),
        ('general', 'General Promo'),
    ]

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    # Basic coupon info
    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Coupon code (e.g., BETA50, WELCOME10)")
    name_en = models.CharField(max_length=100, help_text="Coupon name in English")
    name_ar = models.CharField(max_length=100, help_text="Coupon name in Arabic")
    description_en = models.TextField(blank=True, null=True, help_text="Coupon description in English")
    description_ar = models.TextField(blank=True, null=True, help_text="Coupon description in Arabic")

    # Coupon type and discount
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES, default='general')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text="Discount amount (percentage or fixed KWD amount)"
    )

    # Usage limits
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this coupon can be used (null = unlimited)"
    )
    current_uses = models.PositiveIntegerField(default=0, help_text="Number of times this coupon has been used")
    max_uses_per_user = models.PositiveIntegerField(
        default=1,
        help_text="Maximum uses per user"
    )

    # Order requirements
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount required to use this coupon (KWD)"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Maximum discount amount for percentage-based coupons (KWD)"
    )

    # Validity period
    valid_from = models.DateTimeField(default=timezone.now, help_text="Coupon valid from this date")
    valid_until = models.DateTimeField(null=True, blank=True, help_text="Coupon valid until this date (null = no expiry)")

    # Status
    is_active = models.BooleanField(default=True, help_text="Is this coupon currently active?")

    # Card coupon specific fields
    is_featured = models.BooleanField(default=False, help_text="Show as featured card promo")
    card_color = models.CharField(max_length=7, blank=True, null=True, help_text="Hex color for card display (e.g., #FF5733)")
    card_icon = models.CharField(max_length=100, blank=True, null=True, help_text="Icon name for card display")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

    def __str__(self):
        return f"{self.code} - {self.name_en}"

    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()

        # Check if active
        if not self.is_active:
            return False, "Coupon is not active"

        # Check if started
        if self.valid_from and now < self.valid_from:
            return False, "Coupon is not yet valid"

        # Check if expired
        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired"

        # Check usage limit
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False, "Coupon usage limit reached"

        return True, "Valid"

    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            # Apply max discount cap if set
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
            return float(discount)
        else:  # fixed
            return float(self.discount_value)

    def can_be_used_by_user(self, user_id, order_amount):
        """Check if coupon can be used by a specific user for a specific order amount"""
        # Check basic validity
        is_valid, message = self.is_valid()
        if not is_valid:
            return False, message

        # Check minimum order amount
        if order_amount < self.min_order_amount:
            return False, f"Minimum order amount is {self.min_order_amount} KWD"

        # Check user usage limit
        user_uses = CouponUsage.objects.filter(coupon=self, user_id=user_id).count()
        if user_uses >= self.max_uses_per_user:
            return False, "You have already used this coupon the maximum number of times"

        return True, "Can be used"


class CouponUsage(models.Model):
    """Track coupon usage by users"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user_id = models.CharField(max_length=255, db_index=True, help_text="User ID who used the coupon")
    order_id = models.CharField(max_length=255, blank=True, null=True, help_text="Order ID where coupon was used")

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Actual discount amount applied (KWD)"
    )
    order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Order amount before discount (KWD)"
    )

    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
        indexes = [
            models.Index(fields=['user_id', 'coupon']),
            models.Index(fields=['order_id']),
        ]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user_id} on {self.used_at.strftime('%Y-%m-%d')}"
