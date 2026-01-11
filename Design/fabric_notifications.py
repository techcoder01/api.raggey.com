"""
Fabric Update Notifications via Firebase Cloud Messaging (FCM)

This module sends real-time signals to Flutter app when fabric data changes.
Firebase is used ONLY for signaling - the app fetches actual data from REST API.

Update Types:
- fabric_list_update: When fabrics are added/removed/hidden
- fabric_detail_update: When specific fabric details change (price, name, etc.)
- fabric_color_update: When fabric colors are updated
"""

from firebase_admin import messaging
from User.models import Profile
import logging

logger = logging.getLogger(__name__)


def send_fabric_list_update_notification():
    """
    Send notification when fabric list changes (add/remove/hide fabric).

    Use cases:
    - New fabric added
    - Fabric deleted
    - Fabric hidden/shown (isHidden field changed)
    - Fabric order changed

    The Flutter app will fetch fresh fabric list from API when receiving this signal.
    """
    try:
        # Get all active FCM tokens
        tokens = Profile.objects.filter(
            fcm_token__isnull=False
        ).exclude(
            fcm_token=''
        ).values_list('fcm_token', flat=True)

        tokens = list(tokens)

        if not tokens:
            logger.warning("No FCM tokens found for fabric list update notification")
            return

        # Create FCM message with data payload (silent notification)
        message = messaging.MulticastMessage(
            tokens=tokens,
            data={
                'type': 'fabric_list_update',
            },
        )

        # Send to all devices
        response = messaging.send_multicast(message)

        logger.info(
            f'✅ Fabric list update notification sent successfully: '
            f'{response.success_count}/{len(tokens)} devices'
        )

        if response.failure_count > 0:
            logger.warning(f'⚠️ Failed to send to {response.failure_count} devices')

        return response

    except Exception as e:
        logger.error(f'❌ Error sending fabric list update notification: {e}')
        return None


def send_fabric_detail_update_notification(fabric_id):
    """
    Send notification when specific fabric details change.

    Args:
        fabric_id (int): The ID of the fabric that was updated

    Use cases:
    - Fabric price changed
    - Fabric name changed
    - Fabric attributes updated (season, category, features, etc.)
    - Softness grade changed

    The Flutter app will fetch fresh details for this specific fabric from API.
    """
    try:
        # Get all active FCM tokens
        tokens = Profile.objects.filter(
            fcm_token__isnull=False
        ).exclude(
            fcm_token=''
        ).values_list('fcm_token', flat=True)

        tokens = list(tokens)

        if not tokens:
            logger.warning(f"No FCM tokens found for fabric {fabric_id} update notification")
            return

        # Create FCM message with data payload
        message = messaging.MulticastMessage(
            tokens=tokens,
            data={
                'type': 'fabric_detail_update',
                'fabric_id': str(fabric_id),
            },
        )

        # Send to all devices
        response = messaging.send_multicast(message)

        logger.info(
            f'✅ Fabric #{fabric_id} detail update notification sent successfully: '
            f'{response.success_count}/{len(tokens)} devices'
        )

        if response.failure_count > 0:
            logger.warning(f'⚠️ Failed to send to {response.failure_count} devices')

        return response

    except Exception as e:
        logger.error(f'❌ Error sending fabric detail update notification: {e}')
        return None


def send_fabric_color_update_notification():
    """
    Send notification when fabric colors are updated.

    Use cases:
    - New color added to any fabric
    - Color removed
    - Color stock status changed
    - Color price adjustment changed

    The Flutter app will refresh fabric data to get updated color information.
    """
    try:
        # Get all active FCM tokens
        tokens = Profile.objects.filter(
            fcm_token__isnull=False
        ).exclude(
            fcm_token=''
        ).values_list('fcm_token', flat=True)

        tokens = list(tokens)

        if not tokens:
            logger.warning("No FCM tokens found for fabric color update notification")
            return

        # Create FCM message with data payload
        message = messaging.MulticastMessage(
            tokens=tokens,
            data={
                'type': 'fabric_color_update',
            },
        )

        # Send to all devices
        response = messaging.send_multicast(message)

        logger.info(
            f'✅ Fabric color update notification sent successfully: '
            f'{response.success_count}/{len(tokens)} devices'
        )

        if response.failure_count > 0:
            logger.warning(f'⚠️ Failed to send to {response.failure_count} devices')

        return response

    except Exception as e:
        logger.error(f'❌ Error sending fabric color update notification: {e}')
        return None


def send_main_category_update_notification():
    """
    Send notification when main categories (home page) change.
    
    Use cases:
    - New category added
    - Category deleted
    - Category hidden/shown
    - Category fields (name, price, duration) changed
    """
    try:
        # Get all active FCM tokens
        tokens = Profile.objects.filter(
            fcm_token__isnull=False
        ).exclude(
            fcm_token=''
        ).values_list('fcm_token', flat=True)

        tokens = list(tokens)

        if not tokens:
            logger.warning("No FCM tokens found for main category update notification")
            return

        # Create FCM message with data payload
        message = messaging.MulticastMessage(
            tokens=tokens,
            data={
                'type': 'main_category_update',
            },
        )

        # Send to all devices
        response = messaging.send_multicast(message)

        logger.info(
            f'✅ Main category update notification sent successfully: '
            f'{response.success_count}/{len(tokens)} devices'
        )

        return response

    except Exception as e:
        logger.error(f'❌ Error sending main category update notification: {e}')
        return None


# ============================================================================
# Convenience Functions for Common Admin Actions
# ============================================================================

def notify_fabric_created():
    """Called when a new fabric is created in admin."""
    logger.info("📦 New fabric created - sending notification...")
    return send_fabric_list_update_notification()


def notify_fabric_deleted():
    """Called when a fabric is deleted in admin."""
    logger.info("🗑️ Fabric deleted - sending notification...")
    return send_fabric_list_update_notification()


def notify_fabric_updated(fabric_id):
    """Called when a fabric's details are updated in admin."""
    logger.info(f"📝 Fabric #{fabric_id} updated - sending notification...")
    return send_fabric_detail_update_notification(fabric_id)


def notify_fabric_hidden_changed(fabric_id, is_hidden):
    """Called when a fabric's isHidden status changes."""
    status = "hidden" if is_hidden else "shown"
    logger.info(f"👁️ Fabric #{fabric_id} {status} - sending notification...")
    return send_fabric_list_update_notification()


def notify_fabric_color_created():
    """Called when a new fabric color is created."""
    logger.info("🎨 New fabric color created - sending notification...")
    return send_fabric_color_update_notification()


def notify_fabric_color_updated():
    """Called when a fabric color is updated."""
    logger.info("🎨 Fabric color updated - sending notification...")
    return send_fabric_color_update_notification()


def notify_fabric_color_deleted():
    """Called when a fabric color is deleted."""
    logger.info("🎨 Fabric color deleted - sending notification...")
    return send_fabric_color_update_notification()


# ============================================================================
# Bulk Operations
# ============================================================================

def notify_bulk_fabric_update():
    """Called after bulk fabric operations (bulk edit, import, etc.)."""
    logger.info("📦 Bulk fabric update - sending notification...")
    return send_fabric_list_update_notification()


def notify_bulk_color_update():
    """Called after bulk color operations."""
    logger.info("🎨 Bulk color update - sending notification...")
    return send_fabric_color_update_notification()


def notify_main_category_changed():
    """Called when main categories are changed in admin."""
    logger.info("🏠 Main categories updated - sending notification...")
    return send_main_category_update_notification()
