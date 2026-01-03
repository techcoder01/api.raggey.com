"""
Management command to send cart abandonment notifications
Run this as a cron job every hour to check for abandoned carts and send reminders

Usage:
    python manage.py send_cart_abandoned_notifications

Cron setup (runs every hour):
    0 * * * * cd /path/to/api.raggey.com && python manage.py send_cart_abandoned_notifications
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from Notification.models import CartAbandonmentTracker
from Notification.notification_utils import send_cart_abandoned_notification


class Command(BaseCommand):
    help = 'Send cart abandonment notifications for carts left for 24+ hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending notifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No notifications will be sent'))

        # Find carts that need abandonment notifications
        abandoned_carts = CartAbandonmentTracker.objects.filter(
            notification_sent=False,
            order_completed=False,
        )

        total_carts = abandoned_carts.count()
        self.stdout.write(f'\n📊 Found {total_carts} abandoned carts to check...\n')

        sent_count = 0
        skipped_count = 0

        for cart in abandoned_carts:
            # Check if 24 hours have passed
            if not cart.should_send_notification():
                skipped_count += 1
                continue

            user = cart.user
            if not user or not user.fcm_token:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Skip: User {user.user.email if user and user.user else "Unknown"} - No FCM token'
                    )
                )
                skipped_count += 1
                continue

            time_elapsed = timezone.now() - cart.cart_last_updated
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)

            self.stdout.write(
                f'📦 Cart abandoned {hours_elapsed}h ago: '
                f'{user.user.email if user.user else "Unknown"} - '
                f'{cart.cart_items_count} items ({cart.cart_total} KWD)'
            )

            if not dry_run:
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

                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Notification sent successfully')
                    )
                    sent_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Failed to send notification')
                    )
                    skipped_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Would send notification (dry run)')
                )
                sent_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ DRY RUN COMPLETE: Would send {sent_count} notifications'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ COMPLETE: Sent {sent_count} cart abandonment notifications'
                )
            )
        self.stdout.write(f'⏭️  Skipped: {skipped_count} carts')
        self.stdout.write('=' * 60 + '\n')
