# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pageview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.TextField(editable=False)),
                ('referer', models.TextField(null=True, editable=False)),
                ('query_string', models.TextField(null=True, editable=False)),
                ('method', models.CharField(max_length=20, null=True)),
                ('view_time', models.DateTimeField()),
            ],
            options={
                'ordering': ('-view_time',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Visitor',
            fields=[
                ('session_key', models.CharField(max_length=40, serialize=False, primary_key=True)),
                ('ip_address', models.CharField(max_length=39, editable=False)),
                ('user_agent', models.TextField(null=True, editable=False)),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('expiry_age', models.IntegerField(null=True, editable=False)),
                ('expiry_time', models.DateTimeField(null=True, editable=False)),
                ('time_on_site', models.IntegerField(null=True, editable=False)),
                ('end_time', models.DateTimeField(null=True, editable=False)),
                ('user', models.ForeignKey(related_name='visit_history', editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-start_time',),
                'permissions': (('view_visitor', 'Can view visitor'),),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='pageview',
            name='visitor',
            field=models.ForeignKey(related_name='pageviews', to='tracking.Visitor'),
            preserve_default=True,
        ),
    ]
