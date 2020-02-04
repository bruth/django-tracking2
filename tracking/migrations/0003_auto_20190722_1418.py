# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0002_auto_20180918_2014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pageview',
            name='view_time',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='visitor',
            name='start_time',
            field=models.DateTimeField(editable=False, default=django.utils.timezone.now, db_index=True),
        ),
    ]