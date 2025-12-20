# Generated manually for discount feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Purchase', '0015_cancellationrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='discount_percentage',
            field=models.IntegerField(blank=True, help_text='Discount percentage (15, 5, or 2)', null=True),
        ),
    ]
