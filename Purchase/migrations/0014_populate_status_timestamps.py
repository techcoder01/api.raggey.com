# Generated migration to populate status timestamps for existing orders
from django.db import migrations
from django.utils import timezone


def populate_timestamps(apps, schema_editor):
    """
    Set pending_at to timestamp (order creation time) for all existing orders.
    This ensures existing orders have at least the pending timestamp set.
    """
    Purchase = apps.get_model('Purchase', 'Purchase')

    # Update all orders that don't have pending_at set
    for purchase in Purchase.objects.filter(pending_at__isnull=True):
        purchase.pending_at = purchase.timestamp
        purchase.save(update_fields=['pending_at'])

    print(f"✅ Populated pending_at for {Purchase.objects.filter(pending_at__isnull=False).count()} orders")


def reverse_populate(apps, schema_editor):
    """Reverse migration - clear the timestamps"""
    Purchase = apps.get_model('Purchase', 'Purchase')
    Purchase.objects.all().update(pending_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ('Purchase', '0013_purchase_cancelled_at_purchase_confirmed_at_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_timestamps, reverse_populate),
    ]
