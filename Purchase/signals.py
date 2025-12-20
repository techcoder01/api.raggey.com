from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Purchase
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials
import os


# Initialize Firebase Admin SDK (do this only once)
def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        try:
            # Path to your Firebase service account key
            cred_path = os.path.join(os.path.dirname(__file__), '..', 'firebase-admin-key.json')

            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized")
            else:
                print(f"⚠️ Firebase credentials not found at {cred_path}")
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")


# Initialize on module load
initialize_firebase()


@receiver(pre_save, sender=Purchase)
def track_status_change(sender, instance, **kwargs):
    """Track if order status has changed and set status timestamps"""
    from django.utils import timezone

    if instance.pk:  # Only for existing orders
        try:
            old_instance = Purchase.objects.get(pk=instance.pk)
            instance._status_changed = old_instance.status != instance.status
            instance._old_status = old_instance.status

            # Set timestamp for the new status
            if instance._status_changed:
                now = timezone.now()
                if instance.status == 'Pending' and not instance.pending_at:
                    instance.pending_at = now
                elif instance.status == 'Confirmed' and not instance.confirmed_at:
                    instance.confirmed_at = now
                elif instance.status == 'Working' and not instance.working_at:
                    instance.working_at = now
                elif instance.status == 'Shipping' and not instance.shipping_at:
                    instance.shipping_at = now
                elif instance.status == 'Delivered' and not instance.delivered_at:
                    instance.delivered_at = now
                elif instance.status == 'Cancelled' and not instance.cancelled_at:
                    instance.cancelled_at = now

        except Purchase.DoesNotExist:
            instance._status_changed = False
    else:
        # New order - set pending_at to creation time
        from django.utils import timezone
        instance._status_changed = False
        if instance.status == 'Pending' and not instance.pending_at:
            instance.pending_at = timezone.now()


@receiver(post_save, sender=Purchase)
def send_order_status_notification(sender, instance, created, **kwargs):
    """Send FCM notification when order status changes"""

    # Don't send notification for new orders (handled separately)
    if created:
        return

    # Check if status actually changed
    if not getattr(instance, '_status_changed', False):
        return

    # Get user's FCM token
    if not instance.user:
        print(f"⚠️ Order {instance.invoice_number} has no user")
        return

    try:
        # Get FCM token from user profile
        if not hasattr(instance.user, 'profile'):
            print(f"⚠️ User {instance.user.username} has no profile")
            return

        fcm_token = instance.user.profile.fcm_token

        if not fcm_token:
            print(f"⚠️ User {instance.user.username} has no FCM token")
            return

        # Get status display names
        status_messages = {
            'Pending': {'en': 'Awaiting Confirmation', 'ar': 'في انتظار التأكيد'},
            'Confirmed': {'en': 'Order Confirmed', 'ar': 'تم تأكيد الطلب'},
            'Working': {'en': 'Working on it', 'ar': 'جاري العمل عليه'},
            'Shipping': {'en': 'On the way', 'ar': 'في الطريق'},
            'Delivered': {'en': 'Delivered', 'ar': 'تم التوصيل'},
            'Cancelled': {'en': 'Cancelled', 'ar': 'ملغي'},
        }

        status_info = status_messages.get(instance.status, {'en': instance.status, 'ar': instance.status})

        # Create FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Status Updated',
                body=f'Your order {instance.invoice_number} is now {status_info["en"]}',
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(instance.id),
                'order_number': instance.invoice_number,
                'status': instance.status,
                'status_en': status_info['en'],
                'status_ar': status_info['ar'],
            },
            token=fcm_token,
        )

        # Send message
        response = messaging.send(message)
        print(f"✅ FCM notification sent for order {instance.invoice_number}: {response}")

    except Exception as e:
        print(f"❌ Error sending FCM notification: {e}")
