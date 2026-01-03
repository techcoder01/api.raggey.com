"""
Raggey Notification System
Complete notification utilities for all notification types:
- Order Lifecycle: Placed, Confirmed, Packed, Out for Delivery, Delivered, Cancelled
- Payment: Success, Failed
- Cart Abandoned: 24hr reminder
- Promotional: Admin-controlled messages
"""

import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings
from django.utils import timezone


# Initialize Firebase Admin SDK (if not already initialized)
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            cred_path = os.path.join(settings.BASE_DIR, 'firebase_service_account.json')

            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized")
            else:
                print("⚠️ Warning: firebase_service_account.json not found")
                print(f"Expected path: {cred_path}")
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")


def log_notification(notification_type, priority, channel, user, title, body, order_id=None, promotional_notification=None, was_sent=False, error_message=None):
    """Log notification to database"""
    try:
        from Notification.models import NotificationLog

        log = NotificationLog.objects.create(
            notification_type=notification_type,
            priority=priority,
            channel=channel,
            user=user,
            title=title,
            body=body,
            order_id=order_id,
            promotional_notification=promotional_notification,
            was_sent=was_sent,
            error_message=error_message,
            sent_at=timezone.now() if was_sent else None,
        )
        return log
    except Exception as e:
        print(f"❌ Error logging notification: {e}")
        return None


# ========== ORDER LIFECYCLE NOTIFICATIONS ==========

def send_order_placed_notification(user_fcm_token, order, user_profile=None):
    """
    Order Placed - High Priority - Email/Push
    Sent when order is placed and payment authorized
    """
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Received ✅',
                body=f'Order #{order.invoice_number} received. Payment authorized successfully.'
            ),
            data={
                'type': 'order_placed',
                'notification_type': 'order_placed',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'pending',
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Order Placed notification sent: {response}')

        # Log notification
        if user_profile:
            log_notification(
                notification_type='order_placed',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Received ✅',
                body=f'Order #{order.invoice_number} received. Payment authorized successfully.',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending order placed notification: {e}')
        if user_profile:
            log_notification(
                notification_type='order_placed',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Received ✅',
                body=f'Order #{order.invoice_number} received.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


def send_order_confirmed_notification(user_fcm_token, order, user_profile=None):
    """
    Order Confirmed - Low Priority - Push
    Sent when admin confirms the order
    """
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Confirmed 🎉',
                body=f'Order #{order.invoice_number} confirmed. We\'ll notify you when it\'s ready for delivery.'
            ),
            data={
                'type': 'order_confirmed',
                'notification_type': 'order_confirmed',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'confirmed',
                'priority': 'low',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Order Confirmed notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='order_confirmed',
                priority='low',
                channel='push',
                user=user_profile,
                title='Order Confirmed 🎉',
                body=f'Order #{order.invoice_number} confirmed. We\'ll notify you when it\'s ready for delivery.',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending order confirmed notification: {e}')
        if user_profile:
            log_notification(
                notification_type='order_confirmed',
                priority='low',
                channel='push',
                user=user_profile,
                title='Order Confirmed 🎉',
                body=f'Order #{order.invoice_number} confirmed.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


def send_order_packed_notification(user_fcm_token, order, user_profile=None):
    """
    Order Packed - Low Priority - Push
    Sent when order is packed and ready for delivery
    """
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Packed 📦',
                body=f'Your order #{order.invoice_number} is packed and ready for delivery.'
            ),
            data={
                'type': 'order_packed',
                'notification_type': 'order_packed',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'packed',
                'priority': 'low',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Order Packed notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='order_packed',
                priority='low',
                channel='push',
                user=user_profile,
                title='Order Packed 📦',
                body=f'Your order #{order.invoice_number} is packed and ready for delivery.',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending order packed notification: {e}')
        if user_profile:
            log_notification(
                notification_type='order_packed',
                priority='low',
                channel='push',
                user=user_profile,
                title='Order Packed 📦',
                body=f'Your order #{order.invoice_number} is packed.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


def send_out_for_delivery_notification(user_fcm_token, order, user_profile=None):
    """
    Out for Delivery - High Priority - Push
    Sent when courier marks package as out for delivery
    """
    try:
        initialize_firebase()

        delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else 'today'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Out for Delivery 🚚',
                body=f'Your package is out for delivery today. Expected delivery: {delivery_date}'
            ),
            data={
                'type': 'out_for_delivery',
                'notification_type': 'out_for_delivery',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'shipping',
                'delivery_date': delivery_date,
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Out for Delivery notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='out_for_delivery',
                priority='high',
                channel='push',
                user=user_profile,
                title='Out for Delivery 🚚',
                body=f'Your package is out for delivery today. Expected delivery: {delivery_date}',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending out for delivery notification: {e}')
        if user_profile:
            log_notification(
                notification_type='out_for_delivery',
                priority='high',
                channel='push',
                user=user_profile,
                title='Out for Delivery 🚚',
                body=f'Your package is out for delivery.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


def send_order_delivered_notification(user_fcm_token, order, user_profile=None):
    """
    Order Delivered - High Priority - Push/Email
    Sent when order is delivered
    """
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Delivered ✅',
                body=f'Your order #{order.invoice_number} has been delivered. Thank you for shopping with us!'
            ),
            data={
                'type': 'order_delivered',
                'notification_type': 'order_delivered',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'delivered',
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Order Delivered notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='order_delivered',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Delivered ✅',
                body=f'Your order #{order.invoice_number} has been delivered. Thank you for shopping with us!',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending order delivered notification: {e}')
        if user_profile:
            log_notification(
                notification_type='order_delivered',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Delivered ✅',
                body=f'Your order #{order.invoice_number} has been delivered.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


def send_order_cancelled_notification(user_fcm_token, order, reason=None, user_profile=None):
    """
    Order Cancelled - High Priority - Push/Email
    Sent when order is cancelled
    """
    try:
        initialize_firebase()

        body_text = f'Your order #{order.invoice_number} has been cancelled.'
        if reason:
            body_text += f' Reason: {reason}'
        else:
            body_text += ' Refund will be processed within 3-5 business days.'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Cancelled ❌',
                body=body_text
            ),
            data={
                'type': 'order_cancelled',
                'notification_type': 'order_cancelled',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'cancelled',
                'reason': reason or '',
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Order Cancelled notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='order_cancelled',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Cancelled ❌',
                body=body_text,
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending order cancelled notification: {e}')
        if user_profile:
            log_notification(
                notification_type='order_cancelled',
                priority='high',
                channel='push',
                user=user_profile,
                title='Order Cancelled ❌',
                body=f'Your order #{order.invoice_number} has been cancelled.',
                order_id=order.id,
                was_sent=False,
                error_message=str(e),
            )
        return False


# ========== PAYMENT NOTIFICATIONS ==========

def send_payment_success_notification(user_fcm_token, order, user_profile=None):
    """Payment Success notification"""
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Payment Confirmed 💳',
                body=f'Payment of {order.total_price} KWD confirmed! Your order #{order.invoice_number} is being prepared.'
            ),
            data={
                'type': 'payment_success',
                'notification_type': 'payment_success',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'amount': str(order.total_price),
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Payment Success notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='payment_success',
                priority='high',
                channel='push',
                user=user_profile,
                title='Payment Confirmed 💳',
                body=f'Payment of {order.total_price} KWD confirmed!',
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending payment success notification: {e}')
        return False


def send_payment_failed_notification(user_fcm_token, order, error_message=None, user_profile=None):
    """Payment Failed notification"""
    try:
        initialize_firebase()

        body_text = f'Payment failed for order #{order.invoice_number}.'
        if error_message:
            body_text += f' {error_message}'
        else:
            body_text += ' Please retry or use another payment method.'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Payment Failed ❌',
                body=body_text
            ),
            data={
                'type': 'payment_failed',
                'notification_type': 'payment_failed',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'error_message': error_message or '',
                'priority': 'high',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Payment Failed notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='payment_failed',
                priority='high',
                channel='push',
                user=user_profile,
                title='Payment Failed ❌',
                body=body_text,
                order_id=order.id,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending payment failed notification: {e}')
        return False


# ========== CART ABANDONED NOTIFICATIONS ==========

def send_cart_abandoned_notification(user_fcm_token, cart_items_count, cart_total, user_profile=None):
    """
    Cart Abandoned - Medium Priority - In-App/Push
    Sent 24 hours after user left items in cart
    """
    try:
        initialize_firebase()

        message = messaging.Message(
            notification=messaging.Notification(
                title='Cart Reminder 🛒',
                body=f'You left {cart_items_count} items in your cart — complete checkout to reserve them!'
            ),
            data={
                'type': 'cart_abandoned',
                'notification_type': 'cart_abandoned',
                'cart_items_count': str(cart_items_count),
                'cart_total': str(cart_total),
                'priority': 'medium',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Cart Abandoned notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='cart_abandoned',
                priority='medium',
                channel='push',
                user=user_profile,
                title='Cart Reminder 🛒',
                body=f'You left {cart_items_count} items in your cart — complete checkout to reserve them!',
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending cart abandoned notification: {e}')
        if user_profile:
            log_notification(
                notification_type='cart_abandoned',
                priority='medium',
                channel='push',
                user=user_profile,
                title='Cart Reminder 🛒',
                body=f'You left {cart_items_count} items in your cart.',
                was_sent=False,
                error_message=str(e),
            )
        return False


# ========== PROMOTIONAL NOTIFICATIONS ==========

def send_promotional_notification(user_fcm_token, title, message, promo_code=None, discount_percentage=None, priority='high', user_profile=None, promotional_notification_obj=None):
    """
    Promotional - Admin Controlled - High Priority - Push/Email
    Admins can send promotional messages anytime
    Examples: "Happy Ramadan", "New Sale: Up to 30% off"
    """
    try:
        initialize_firebase()

        data_payload = {
            'type': 'promotional',
            'notification_type': 'promotional',
            'priority': priority,
        }

        if promo_code:
            data_payload['promo_code'] = promo_code
        if discount_percentage:
            data_payload['discount_percentage'] = str(discount_percentage)

        message_obj = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=message
            ),
            data=data_payload,
            token=user_fcm_token,
        )

        response = messaging.send(message_obj)
        print(f'✅ Promotional notification sent: {response}')

        if user_profile:
            log_notification(
                notification_type='promotional',
                priority=priority,
                channel='push',
                user=user_profile,
                title=title,
                body=message,
                promotional_notification=promotional_notification_obj,
                was_sent=True,
            )

        return True
    except Exception as e:
        print(f'❌ Error sending promotional notification: {e}')
        if user_profile:
            log_notification(
                notification_type='promotional',
                priority=priority,
                channel='push',
                user=user_profile,
                title=title,
                body=message,
                promotional_notification=promotional_notification_obj,
                was_sent=False,
                error_message=str(e),
            )
        return False


# ========== HELPER FUNCTIONS ==========

def send_order_status_notification(user_fcm_token, order, new_status, user_profile=None, **kwargs):
    """
    Main helper function to send appropriate notification based on order status

    Args:
        user_fcm_token: User's FCM token
        order: Purchase/Order object
        new_status: New order status
        user_profile: User Profile object for logging
        **kwargs: Additional parameters (estimated_days, reason, etc.)
    """
    if not user_fcm_token:
        print("⚠️ Warning: No FCM token provided")
        return False

    initialize_firebase()

    status_lower = new_status.lower()

    # Map status to notification function
    status_handlers = {
        'pending': lambda: send_order_placed_notification(user_fcm_token, order, user_profile),
        'placed': lambda: send_order_placed_notification(user_fcm_token, order, user_profile),
        'confirmed': lambda: send_order_confirmed_notification(user_fcm_token, order, user_profile),
        'packed': lambda: send_order_packed_notification(user_fcm_token, order, user_profile),
        'working': lambda: send_order_packed_notification(user_fcm_token, order, user_profile),
        'shipping': lambda: send_out_for_delivery_notification(user_fcm_token, order, user_profile),
        'out_for_delivery': lambda: send_out_for_delivery_notification(user_fcm_token, order, user_profile),
        'delivered': lambda: send_order_delivered_notification(user_fcm_token, order, user_profile),
        'cancelled': lambda: send_order_cancelled_notification(user_fcm_token, order, kwargs.get('reason'), user_profile),
    }

    handler = status_handlers.get(status_lower)
    if handler:
        return handler()
    else:
        print(f"⚠️ Warning: No notification handler for status '{new_status}'")
        return False
