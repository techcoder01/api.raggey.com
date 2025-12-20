# Generated migration to update existing order statuses

from django.db import migrations


def update_order_statuses(apps, schema_editor):
    """Update existing orders from old status names to new status names"""
    Purchase = apps.get_model('Purchase', 'Purchase')

    # Update status values
    Purchase.objects.filter(status='Processing').update(status='Confirmed')
    Purchase.objects.filter(status='Ready').update(status='Working')
    Purchase.objects.filter(status='Delivering').update(status='Shipping')
    Purchase.objects.filter(status='Complete').update(status='Delivered')

    print("✅ Updated order statuses:")
    print(f"  - Processing → Confirmed")
    print(f"  - Ready → Working")
    print(f"  - Delivering → Shipping")
    print(f"  - Complete → Delivered")


def reverse_update(apps, schema_editor):
    """Reverse the status updates if needed"""
    Purchase = apps.get_model('Purchase', 'Purchase')

    # Reverse the updates
    Purchase.objects.filter(status='Confirmed').update(status='Processing')
    Purchase.objects.filter(status='Working').update(status='Ready')
    Purchase.objects.filter(status='Shipping').update(status='Delivering')
    Purchase.objects.filter(status='Delivered').update(status='Complete')


class Migration(migrations.Migration):

    dependencies = [
        ('Purchase', '0011_alter_purchase_status'),
    ]

    operations = [
        migrations.RunPython(update_order_statuses, reverse_update),
    ]
