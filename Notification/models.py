from django.db import models
from django.utils import timezone
from User.models import Profile


class NotificationType(models.TextChoices):
    """Notification type choices"""
    ORDER_PLACED = 'order_placed', 'Order Placed'
    ORDER_CONFIRMED = 'order_confirmed', 'Order Confirmed'
    ORDER_PACKED = 'order_packed', 'Order Packed'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    ORDER_DELIVERED = 'order_delivered', 'Order Delivered'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
    CART_ABANDONED = 'cart_abandoned', 'Cart Abandoned'
    PROMOTIONAL = 'promotional', 'Promotional Offer'
    PAYMENT_SUCCESS = 'payment_success', 'Payment Success'
    PAYMENT_FAILED = 'payment_failed', 'Payment Failed'


class NotificationPriority(models.TextChoices):
    """Notification priority levels"""
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'


class NotificationChannel(models.TextChoices):
    """Notification delivery channels"""
    PUSH = 'push', 'Push Notification'
    EMAIL = 'email', 'Email'
    IN_APP = 'in_app', 'In-App'


class PromotionalNotification(models.Model):
    """
    Admin-controlled promotional notifications
    Admins can create and send promotional messages to users anytime
    """
    title = models.CharField(max_length=200, help_text="Notification title (e.g., 'Happy Ramadan!')")
    message = models.TextField(help_text="Notification message body")

    # Targeting
    send_to_all = models.BooleanField(
        default=True,
        help_text="Send to all users? If unchecked, select specific users below"
    )
    target_users = models.ManyToManyField(
        Profile,
        blank=True,
        help_text="Select specific users (only if 'Send to all' is unchecked)"
    )

    # Delivery settings
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.HIGH,
    )
    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.PUSH,
        help_text="How to deliver this notification"
    )

    # Optional promotional data
    promo_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional promo code (e.g., 'RAMADAN30')"
    )
    discount_percentage = models.IntegerField(
        blank=True,
        null=True,
        help_text="Optional discount percentage (e.g., 30 for 30% off)"
    )

    # Scheduling
    scheduled_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Schedule for later? Leave blank to send immediately"
    )

    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    sent_count = models.IntegerField(default=0, help_text="Number of users who received this notification")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Admin who created this notification"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promotional Notification'
        verbose_name_plural = 'Promotional Notifications'

    def __str__(self):
        status = "Sent" if self.is_sent else "Pending"
        return f"{self.title} ({status})"

    def send_notification(self):
        """Send this promotional notification to target users"""
        from Notification.notification_utils import send_promotional_notification

        # Get target users
        if self.send_to_all:
            users = Profile.objects.filter(fcm_token__isnull=False).exclude(fcm_token='')
        else:
            users = self.target_users.filter(fcm_token__isnull=False).exclude(fcm_token='')

        # Send to each user
        success_count = 0
        for user in users:
            try:
                success = send_promotional_notification(
                    user_fcm_token=user.fcm_token,
                    title=self.title,
                    message=self.message,
                    promo_code=self.promo_code,
                    discount_percentage=self.discount_percentage,
                    priority=self.priority,
                )
                if success:
                    success_count += 1
            except Exception as e:
                print(f"❌ Error sending notification to user {user.id}: {e}")

        # Update status
        self.is_sent = True
        self.sent_at = timezone.now()
        self.sent_count = success_count
        self.save()

        return success_count


class NotificationLog(models.Model):
    """
    Log of all notifications sent (for analytics and debugging)
    """
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
    )
    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
    )

    # User info
    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='notifications_received',
    )

    # Notification content
    title = models.CharField(max_length=200)
    body = models.TextField()

    # Related objects
    order_id = models.IntegerField(blank=True, null=True)
    promotional_notification = models.ForeignKey(
        PromotionalNotification,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    # Delivery status
    was_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.user.user.email if self.user.user else 'Unknown'} ({self.created_at})"


class CartAbandonmentTracker(models.Model):
    """
    Track cart abandonment for sending reminders after 24 hours
    """
    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='cart_abandonments',
    )

    # Cart info
    cart_items_count = models.IntegerField(default=0)
    cart_total = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Timestamps
    cart_last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Notification status
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)

    # Conversion tracking
    order_completed = models.BooleanField(default=False)
    order_completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-cart_last_updated']
        verbose_name = 'Cart Abandonment'
        verbose_name_plural = 'Cart Abandonments'
        indexes = [
            models.Index(fields=['notification_sent', 'cart_last_updated']),
        ]

    def __str__(self):
        return f"{self.user.user.email if self.user.user else 'Unknown'} - {self.cart_items_count} items"

    def should_send_notification(self):
        """Check if 24 hours have passed and notification hasn't been sent"""
        if self.notification_sent or self.order_completed:
            return False

        # Check if 24 hours have passed
        time_elapsed = timezone.now() - self.cart_last_updated
        return time_elapsed.total_seconds() >= 24 * 60 * 60  # 24 hours in seconds
