"""
FCM Notification Utilities for Raggey Backend
Sends push notifications for critical events:
- Order Status Updates (6 types)
- Payment Confirmations (2 types)
- New Discounts/Promos (1 type)
"""

import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings


# Initialize Firebase Admin SDK (if not already initialized)
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            # Path to service account key file
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


# ========== ORDER STATUS NOTIFICATIONS ==========

def send_order_pending_notification(user_fcm_token, order):
    """Send notification when order is created (Pending status)"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Received',
                body=f'Order #{order.invoice_number} received. Reviewing your custom measurements.'
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'pending',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Pending notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending pending notification: {e}')
        return False


def send_order_confirmed_notification(user_fcm_token, order):
    """Send notification when order is confirmed"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Confirmed',
                body=f'Great news! Order #{order.invoice_number} confirmed. Tailoring begins soon.'
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'confirmed',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Confirmed notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending confirmed notification: {e}')
        return False


def send_order_working_notification(user_fcm_token, order, estimated_days=0):
    """Send notification when order is in production (Working status)"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Tailoring Started',
                body=f'Your dishdasha is being tailored. Ready in {estimated_days} days.' if estimated_days > 0 else 'Your dishdasha is being tailored.'
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'working',
                'estimated_days': str(estimated_days),
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Working notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending working notification: {e}')
        return False


def send_order_shipping_notification(user_fcm_token, order):
    """Send notification when order is shipped"""
    try:
        delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else 'soon'

        message = messaging.Message(
            notification=messaging.Notification(
                title='On the Way!',
                body=f'Your order is on the way! Estimated delivery: {delivery_date}'
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'shipping',
                'delivery_date': delivery_date,
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Shipping notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending shipping notification: {e}')
        return False


def send_order_delivered_notification(user_fcm_token, order):
    """Send notification when order is delivered"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Delivered',
                body=f'Your order has been delivered! Please confirm receipt.'
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'delivered',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Delivered notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending delivered notification: {e}')
        return False


def send_order_cancelled_notification(user_fcm_token, order, reason=None):
    """Send notification when order is cancelled"""
    try:
        body_text = f'Order #{order.invoice_number} cancelled.'
        if reason:
            body_text += f' Reason: {reason}'
        else:
            body_text += ' Refund being processed.'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Order Cancelled',
                body=body_text
            ),
            data={
                'type': 'order_status_update',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'status': 'cancelled',
                'reason': reason or '',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Cancelled notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending cancelled notification: {e}')
        return False


# ========== PAYMENT NOTIFICATIONS ==========

def send_payment_success_notification(user_fcm_token, order):
    """Send notification when payment is successful"""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Payment Confirmed',
                body=f'Payment of {order.total_price} KWD confirmed! Your order #{order.invoice_number} is being prepared.'
            ),
            data={
                'type': 'payment_success',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'amount': str(order.total_price),
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Payment success notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending payment success notification: {e}')
        return False


def send_payment_failed_notification(user_fcm_token, order, error_message=None):
    """Send notification when payment fails"""
    try:
        body_text = f'Payment failed for order #{order.invoice_number}.'
        if error_message:
            body_text += f' {error_message}'
        else:
            body_text += ' Please retry or use another payment method.'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Payment Failed',
                body=body_text
            ),
            data={
                'type': 'payment_failed',
                'order_id': str(order.id),
                'invoice_number': order.invoice_number,
                'error_message': error_message or '',
            },
            token=user_fcm_token,
        )

        response = messaging.send(message)
        print(f'✅ Payment failed notification sent: {response}')
        return True
    except Exception as e:
        print(f'❌ Error sending payment failed notification: {e}')
        return False


# ========== HELPER FUNCTIONS ==========

def send_order_status_notification(user_fcm_token, order, new_status, **kwargs):
    """
    Main helper function to send appropriate notification based on order status

    Args:
        user_fcm_token: User's FCM token
        order: Purchase/Order object
        new_status: New order status
        **kwargs: Additional parameters (estimated_days, reason, etc.)
    """
    if not user_fcm_token:
        print("⚠️ Warning: No FCM token provided")
        return False

    # Initialize Firebase if not already done
    initialize_firebase()

    status_lower = new_status.lower()

    # Map status to notification function
    status_handlers = {
        'pending': lambda: send_order_pending_notification(user_fcm_token, order),
        'confirmed': lambda: send_order_confirmed_notification(user_fcm_token, order),
        'working': lambda: send_order_working_notification(user_fcm_token, order, kwargs.get('estimated_days', 0)),
        'shipping': lambda: send_order_shipping_notification(user_fcm_token, order),
        'delivered': lambda: send_order_delivered_notification(user_fcm_token, order),
        'cancelled': lambda: send_order_cancelled_notification(user_fcm_token, order, kwargs.get('reason')),
    }

    handler = status_handlers.get(status_lower)
    if handler:
        return handler()
    else:
        print(f"⚠️ Warning: No notification handler for status '{new_status}'")
        return False
