from django.db import models
from decimal import *
from django.contrib.auth.models import User
from Design.models import UserDesign
from Sizes.models import Sizes
from User.models import Address
import random
import string
# Create your models here.

STATUS_CHOICES = (
    ("Pending", "Pending"),
    ("Confirmed", "Confirmed"),
    ("Working", "Working"),
    ("Shipping", "Shipping"),
    ("Delivered", "Delivered"),
    ("Cancelled", "Cancelled"),
)

def generate_invoice_number():
    """Generate unique invoice number: INV-YYYYMMDD-XXXX"""
    from datetime import datetime
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"INV-{date_str}-{random_str}"

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', null=True, blank=True)

    # Link to user's saved address - admin can select from user's addresses
    selected_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Select from user's saved addresses (Home/Work/etc.)"
    )

    invoice_number = models.CharField(
        max_length=100, unique=True, default=generate_invoice_number)
    full_name = models.CharField(max_length=200, default='')
    email = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=20, default = '', null=True, blank=True)
    latitude = models.CharField(max_length=20, default = '', null=True, blank=True)
    address_name = models.CharField(max_length=80,blank=True, null=True)
    Area = models.CharField(max_length=150,blank=True, null=True)
    block = models.CharField(max_length=100,blank=True, null=True)
    street = models.CharField(max_length=100,blank=True, null=True)
    house = models.CharField(max_length=100,blank=True, null=True)
    apartment = models.CharField(max_length=10, null=True, blank=True)
    floor = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=13)
    payment_option = models.CharField(max_length=30)
    total_price = models.DecimalField(max_digits=9, decimal_places=3)
    delivery_fee = models.DecimalField(max_digits=9, decimal_places=3, default=Decimal('0.000'))
    discount_amount = models.DecimalField(max_digits=9, decimal_places=3, default=Decimal('0.000'))
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    cancelled_by = models.CharField(max_length=20, blank=True, null=True, choices=[('user', 'User'), ('admin', 'Admin')])
    cancellation_reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES,  default='Pending')

    # Status timestamp tracking
    pending_at = models.DateTimeField(null=True, blank=True, help_text="When order was placed")
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When order was confirmed")
    working_at = models.DateTimeField(null=True, blank=True, help_text="When work started on order")
    shipping_at = models.DateTimeField(null=True, blank=True, help_text="When order was shipped")
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When order was delivered")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="When order was cancelled")

    asap_order_id = models.CharField(max_length=100, null=True, blank=True)
    is_pick_up=models.BooleanField(default=False)
    is_cash =models.BooleanField(default=False)

    def __str__(self):
        return f"{self.invoice_number} - {self.full_name}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
    
class Item(models.Model):
    invoice = models.ForeignKey(
        Purchase, related_name='items', on_delete=models.CASCADE)

    # NEW: Link to UserDesign for custom designs
    user_design = models.ForeignKey(
        UserDesign, on_delete=models.CASCADE, null=True, blank=True, related_name='order_items')

    # NEW: Link to selected size
    selected_size = models.ForeignKey(
        Sizes, on_delete=models.CASCADE, null=True, blank=True)

    product_code = models.CharField(max_length=255, null=True, blank=True)
    product_id = models.IntegerField(null=True, blank=True)  # Made nullable for custom designs
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, default='Custom Design')
    unit_price = models.DecimalField(
        max_digits=9, decimal_places=3, default=Decimal('0.000'))
    net_amount = models.DecimalField(
        max_digits=9, decimal_places=3, default=Decimal('0.000'))
    discount = models.DecimalField(
        max_digits=9, decimal_places=3, default=Decimal('0.000'))
    discount_percentage = models.IntegerField(null=True, blank=True, help_text="Discount percentage (15, 10, or 5)")
    quantity = models.IntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    product_size = models.CharField(max_length=10, null=True, blank=True)
    cover = models.URLField(max_length=600, null=True, blank=True)

    # Store design details as JSON (fabric, collar, buttons, etc.)
    design_details = models.JSONField(null=True, blank=True)

    # Store size details as JSON (measurements)
    size_details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} - {self.invoice.invoice_number}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"


class CancellationRequest(models.Model):
    """
    Cancellation requests that require admin approval
    Used for orders in Working or Shipping status
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    order = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='cancellation_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cancellation_requests')
    reason = models.TextField(help_text="User's reason for cancellation")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin's notes/reason for approval/rejection")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_cancellations')
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Cancellation Request #{self.id} - Order {self.order.invoice_number} - {self.status}"

    class Meta:
        verbose_name = "Cancellation Request"
        verbose_name_plural = "Cancellation Requests"
        ordering = ['-created_at']


class DeliverySettings(models.Model):
    """
    Singleton model for delivery settings (receive within days and delivery cost)
    Only one active settings record should exist
    """
    delivery_days = models.IntegerField(
        default=5,
        help_text="Number of days for delivery (e.g., 'Receive within X days')"
    )
    delivery_cost = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=Decimal('2.000'),
        help_text="Delivery cost in KWD"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one settings record should be active at a time"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery Settings - {self.delivery_days} days, {self.delivery_cost} KWD"

    def save(self, *args, **kwargs):
        """Ensure only one active settings record exists"""
        if self.is_active:
            # Deactivate all other settings
            DeliverySettings.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Delivery Settings"
        verbose_name_plural = "Delivery Settings"
        ordering = ['-is_active', '-updated_at']


# ======================  PAYZAH PAYMENT MODELS ======================

PAYMENT_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('captured', 'Captured'),
    ('failed', 'Failed'),
    ('canceled', 'Canceled'),
    ('refunded', 'Refunded'),
)

class Payment(models.Model):
    """Payment transaction model for Payzah gateway integration"""

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    purchase = models.OneToOneField(Purchase, on_delete=models.CASCADE, related_name='payment', null=True, blank=True)

    # Payment details
    amount = models.DecimalField(max_digits=9, decimal_places=3)
    currency = models.CharField(max_length=3, default='KWD')

    # Payzah specific fields
    track_id = models.CharField(max_length=100, unique=True, db_index=True)
    payzah_payment_id = models.CharField(max_length=100)
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='pending', db_index=True)

    # Payzah response details
    payzah_reference_code = models.CharField(max_length=100, blank=True, null=True)
    knet_payment_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_number = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.CharField(max_length=100, blank=True, null=True)
    payment_status_raw = models.CharField(max_length=50, blank=True, null=True, help_text="Raw status from Payzah")

    # UDF fields (User Defined Fields)
    udf1 = models.CharField(max_length=255, blank=True, null=True)
    udf2 = models.CharField(max_length=255, blank=True, null=True)
    udf3 = models.CharField(max_length=255, blank=True, null=True)
    udf4 = models.CharField(max_length=255, blank=True, null=True)
    udf5 = models.CharField(max_length=255, blank=True, null=True)

    # URLs
    redirect_url = models.URLField(max_length=500, blank=True, null=True)
    success_url = models.URLField(max_length=500, blank=True, null=True)
    error_url = models.URLField(max_length=500, blank=True, null=True)

    # Security fields
    idempotency_key = models.CharField(max_length=200, unique=True, null=True, blank=True, db_index=True)
    verified_with_gateway = models.BooleanField(default=False)
    gateway_verification_attempts = models.IntegerField(default=0)

    # Metadata
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.track_id} - {self.amount} {self.currency} - {self.status}"

    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['track_id']),
            models.Index(fields=['payzah_payment_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
