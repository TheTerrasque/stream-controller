# Generated by Django 4.0.3 on 2022-03-18 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0004_playlist_films'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stream',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='stream',
            name='order',
            field=models.IntegerField(default=100),
        ),
    ]
