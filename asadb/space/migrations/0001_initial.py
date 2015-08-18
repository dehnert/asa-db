# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import space.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LockType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('info_addr', models.EmailField(default=b'asa-exec@mit.edu', help_text=b'Address groups should email to get more information about managing access through this lock type.', max_length=254)),
                ('info_url', models.URLField(help_text=b'URL that groups can visit to get more information about this lock type.', blank=True)),
                ('db_update', models.CharField(default=b'none', max_length=20, choices=[(b'none', b'No database management'), (b'cac-card', b'CAC-managed card-based access')])),
            ],
        ),
        migrations.CreateModel(
            name='Space',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.CharField(unique=True, max_length=20)),
                ('asa_owned', models.BooleanField(default=True)),
                ('merged_acl', models.BooleanField(default=False, help_text=b"Does this room have a single merged ACL, that combines all groups together, or CAC maintain a separate ACL per-group? Generally, the shared storage offices get a merged ACL and everything else doesn't.")),
                ('notes', models.TextField(blank=True)),
                ('lock_type', models.ForeignKey(to='space.LockType')),
            ],
        ),
        migrations.CreateModel(
            name='SpaceAccessListEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField(default=space.models.now_offset, db_index=True)),
                ('end', models.DateTimeField(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999), db_index=True)),
                ('name', models.CharField(max_length=50)),
                ('card_number', models.CharField(help_text=b'MIT ID number (as printed on, eg, the relevant ID card)', max_length=20, verbose_name=b'MIT ID')),
                ('group', models.ForeignKey(to='groups.Group')),
                ('space', models.ForeignKey(to='space.Space')),
            ],
        ),
        migrations.CreateModel(
            name='SpaceAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateField(default=datetime.datetime.now, db_index=True)),
                ('end', models.DateField(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999), db_index=True)),
                ('notes', models.TextField(blank=True)),
                ('locker_num', models.CharField(help_text=b'Locker number. If set, will use the "locker-access" OfficerRole to maintain access. If unset/blank, uses "office-access" and SpaceAccessListEntry for access.', max_length=10, blank=True)),
                ('group', models.ForeignKey(to='groups.Group')),
                ('space', models.ForeignKey(to='space.Space')),
            ],
        ),
    ]
