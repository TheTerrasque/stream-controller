# Generated by Django 4.2.8 on 2024-08-30 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0021_remove_filmstream_special_film_special'),
    ]

    operations = [
        migrations.AddField(
            model_name='film',
            name='status',
            field=models.CharField(default='new', max_length=255),
        ),
    ]