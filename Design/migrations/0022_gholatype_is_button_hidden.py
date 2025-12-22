# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Design', '0021_make_design_fields_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='gholatype',
            name='is_button_hidden',
            field=models.BooleanField(default=False, help_text='If True, button will be rendered below collar (hidden)'),
        ),
    ]
