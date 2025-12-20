from django.core.management.base import BaseCommand
from Purchase.models import DeliverySettings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate default delivery settings'

    def handle(self, *args, **kwargs):
        # Check if settings already exist
        existing_settings = DeliverySettings.objects.filter(is_active=True).first()

        if existing_settings:
            self.stdout.write(
                self.style.WARNING(f'Active delivery settings already exist: {existing_settings}')
            )
            return

        # Create default settings
        settings = DeliverySettings.objects.create(
            delivery_days=5,
            delivery_cost=Decimal('2.000'),
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully created delivery settings: {settings}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   - Delivery Days: {settings.delivery_days}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   - Delivery Cost: {settings.delivery_cost} KWD')
        )
