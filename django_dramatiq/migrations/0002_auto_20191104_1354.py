# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='task',
            managers=[
            ],
        ),
        migrations.AddField(
            model_name='task',
            name='actor_name',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='queue_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='updated_at',
            field=models.DateTimeField(db_index=True, auto_now=True),
        ),
    ]
