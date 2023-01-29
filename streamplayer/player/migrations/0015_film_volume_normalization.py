# Generated by Django 3.2.6 on 2023-01-29 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0014_auto_20230129_0346'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='volume_normalization',
            field=models.CharField(choices=[('d', 'Stream Default'), ('yes', 'On'), ('no', 'Off')], default='d', help_text='Normalize audio volume', max_length=5),
        ),
    ]
