"""
Start background scheduler for cart abandonment notifications
Run this once: python manage.py start_scheduler

This will run in the background and automatically send cart abandoned
notifications every hour without needing external crontab!
"""

import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from Notification.models import CartAbandonmentTracker
from Notification.notification_utils import send_cart_abandoned_notification

logger = logging.getLogger(__name__)


@util.close_old_connections
def send_cart_abandoned_notifications_job():
    """
    Background job to send cart abandonment notifications
    Runs every hour automatically
    """
    logger.info("🔍 Checking for abandoned carts...")

    # Find carts that need abandonment notifications
    abandoned_carts = CartAbandonmentTracker.objects.filter(
        notification_sent=False,
        order_completed=False,
    )

    sent_count = 0

    for cart in abandoned_carts:
        # Check if 24 hours have passed
        if not cart.should_send_notification():
            continue

        user = cart.user
        if not user or not user.fcm_token:
            continue

        # Send notification
        success = send_cart_abandoned_notification(
            user_fcm_token=user.fcm_token,
            cart_items_count=cart.cart_items_count,
            cart_total=cart.cart_total,
            user_profile=user,
        )

        if success:
            # Mark as sent
            cart.notification_sent = True
            cart.notification_sent_at = timezone.now()
            cart.save()
            sent_count += 1
            logger.info(f"✅ Cart abandoned notification sent to {user.user.email if user.user else 'Unknown'}")

    logger.info(f"📊 Sent {sent_count} cart abandonment notifications")


# This decorator ensures that if a job execution fails, it won't stop the scheduler
@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Delete old job execution logs (older than 1 week by default)
    Runs daily to keep database clean
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Starts the APScheduler background task scheduler for cart abandonment notifications"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Add cart abandonment check job - runs every hour
        scheduler.add_job(
            send_cart_abandoned_notifications_job,
            trigger=CronTrigger(minute=0),  # Every hour at :00
            id="send_cart_abandoned_notifications",  # Unique ID
            max_instances=1,
            replace_existing=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "✅ Added job: 'send_cart_abandoned_notifications' - runs every hour"
            )
        )

        # Add job to delete old job executions - runs daily at 12:00 AM
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(hour=0, minute=0),  # Daily at midnight
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "✅ Added job: 'delete_old_job_executions' - runs daily at midnight"
            )
        )

        self.stdout.write(
            self.style.SUCCESS("\n" + "="*60)
        )
        self.stdout.write(
            self.style.SUCCESS("🚀 Scheduler started! Cart abandonment notifications will run automatically every hour.")
        )
        self.stdout.write(
            self.style.SUCCESS("📊 Press Ctrl+C to exit")
        )
        self.stdout.write(
            self.style.SUCCESS("="*60 + "\n")
        )

        try:
            scheduler.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n⚠️ Scheduler stopped by user"))
            scheduler.shutdown()
            self.stdout.write(self.style.SUCCESS("✅ Scheduler shut down successfully"))
