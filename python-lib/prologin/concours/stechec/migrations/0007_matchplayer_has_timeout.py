# Generated by Django 2.2.10 on 2020-03-01 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stechec', '0006_tournamentplayercorrection'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchplayer',
            name='has_timeout',
            field=models.BooleanField(
                default=False, verbose_name='has timeout'
            ),
        ),
    ]
