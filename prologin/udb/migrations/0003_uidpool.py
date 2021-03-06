# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-05 18:44
from __future__ import unicode_literals

from django.db import migrations, models
import django_prometheus.models


def initial_data(apps, schema_editor):
    UIDPool = apps.get_model('udb', 'UIDPool')
    UIDPool(last=0, group="user", base=10000, pk=1).save()
    UIDPool(last=0, group="orga", base=11000, pk=2).save()
    UIDPool(last=0, group="root", base=12000, pk=3).save()


class Migration(migrations.Migration):

    dependencies = [
        ('udb', '0002_initial_data'),
    ]

    operations = [migrations.RunPython(initial_data)]
