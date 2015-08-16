# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import mit
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'activity categories',
            },
        ),
        migrations.CreateModel(
            name='AthenaMoiraAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=8)),
                ('mit_id', models.CharField(max_length=15)),
                ('first_name', models.CharField(max_length=45)),
                ('last_name', models.CharField(max_length=45)),
                ('account_class', models.CharField(max_length=10)),
                ('affiliation_basic', models.CharField(max_length=10)),
                ('affiliation_detailed', models.CharField(max_length=40)),
                ('loose_student', models.BooleanField(default=False, help_text=b'Whether to use loose or strict determination of student status. Loose means that either the account class or the affiliation should indicate student status; strict means that the affiliation must be student. In general, we use strict; for some people ("secret people") directory information is suppressed and the affiliation will be misleading.')),
                ('mutable', models.BooleanField(default=True)),
                ('add_date', models.DateField(help_text=b'Date when this person was added to the dump.')),
                ('del_date', models.DateField(help_text=b'Date when this person was removed from the dump.', null=True, blank=True)),
                ('mod_date', models.DateField(help_text=b"Date when this person's record was last changed.", null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Athena (Moira) account',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('abbreviation', models.CharField(db_index=True, max_length=10, blank=True)),
                ('description', models.TextField(blank=True)),
                ('website_url', models.URLField(blank=True)),
                ('constitution_url', models.CharField(blank=True, max_length=200, validators=[mit.UrlOrAfsValidator])),
                ('meeting_times', models.TextField(blank=True)),
                ('advisor_name', models.CharField(max_length=100, blank=True)),
                ('num_undergrads', models.IntegerField(null=True, blank=True)),
                ('num_grads', models.IntegerField(null=True, blank=True)),
                ('num_community', models.IntegerField(null=True, blank=True)),
                ('num_other', models.IntegerField(null=True, blank=True)),
                ('group_email', models.EmailField(max_length=254, verbose_name=b'group email list', blank=True)),
                ('officer_email', models.EmailField(max_length=254, verbose_name=b"officers' email list")),
                ('main_account_id', models.IntegerField(null=True, blank=True)),
                ('funding_account_id', models.IntegerField(null=True, blank=True)),
                ('athena_locker', models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(regex=b'^[-A-Za-z0-9_.]+$', message=b'Enter a valid Athena locker. This should be the single "word" that appears in "/mit/word/" or "web.mit.edu/word/", with no slashes, spaces, etc..')])),
                ('recognition_date', models.DateTimeField()),
                ('update_date', models.DateTimeField(editable=False)),
                ('updater', models.CharField(max_length=30, null=True, editable=False)),
                ('activity_category', models.ForeignKey(blank=True, to='groups.ActivityCategory', null=True)),
            ],
            options={
                'ordering': ('name',),
                'permissions': (('view_group_private_info', 'View private group information'), ('admin_group', 'Administer basic group information'), ('view_signatories', 'View signatory information for all groups'), ('recognize_nge', 'Recognize Non-Group Entity'), ('recognize_group', 'Recognize groups')),
            },
        ),
        migrations.CreateModel(
            name='GroupClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('gets_publicity', models.BooleanField(default=False, help_text=b'Gets publicity resources such as FYSM or Activities Midway')),
            ],
            options={
                'verbose_name_plural': 'group classes',
            },
        ),
        migrations.CreateModel(
            name='GroupConstitution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_url', models.URLField()),
                ('dest_file', models.CharField(max_length=100)),
                ('last_update', models.DateTimeField(help_text=b'Last time when this constitution actually changed.')),
                ('last_download', models.DateTimeField(help_text=b'Last time we downloaded this constitution to see if it had changed.')),
                ('failure_date', models.DateTimeField(default=None, help_text=b'Time this URL started failing to download. (Null if currently working.)', null=True, blank=True)),
                ('status_msg', models.CharField(max_length=100)),
                ('failure_reason', models.CharField(default=b'', max_length=100, blank=True)),
                ('group', models.ForeignKey(to='groups.Group', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupFunding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('contact_email', models.EmailField(max_length=254)),
                ('funding_list', models.CharField(help_text=b'List that groups receiving funding emails should be on. The database will attempt to make sure that ONLY those groups are on it.', max_length=32, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=30, db_index=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('body', models.TextField()),
                ('acl_read_group', models.BooleanField(default=True, help_text=b'Can the group read this note')),
                ('acl_read_offices', models.BooleanField(default=True, help_text=b'Can "offices" that interact with groups (SAO, CAC, and funding boards) read this note')),
                ('group', models.ForeignKey(to='groups.Group')),
            ],
            options={
                'permissions': (('view_note_group', 'View notes intended for the group to see'), ('view_note_office', 'View notes intended for "offices" to see'), ('view_note_all', 'View all notes')),
            },
        ),
        migrations.CreateModel(
            name='GroupStartup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stage', models.IntegerField(choices=[(10, b'submitted'), (20, b'approved'), (-10, b'rejected')])),
                ('submitter', models.CharField(max_length=30, editable=False)),
                ('create_officer_list', models.BooleanField(default=False)),
                ('create_group_list', models.BooleanField(default=False)),
                ('create_athena_locker', models.BooleanField(default=True)),
                ('president_name', models.CharField(max_length=50)),
                ('president_kerberos', models.CharField(max_length=8)),
                ('treasurer_name', models.CharField(max_length=50)),
                ('treasurer_kerberos', models.CharField(max_length=8)),
                ('group', models.ForeignKey(to='groups.Group', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True, help_text=b'This status represents an active group')),
            ],
            options={
                'verbose_name_plural': 'group statuses',
            },
        ),
        migrations.CreateModel(
            name='OfficeHolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person', models.CharField(help_text=b'Athena username', max_length=30, db_index=True)),
                ('start_time', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('end_time', models.DateTimeField(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999), db_index=True)),
                ('group', models.ForeignKey(to='groups.Group')),
            ],
        ),
        migrations.CreateModel(
            name='OfficerRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('max_count', models.IntegerField(default=10000, help_text=b'Maximum number of holders of this role. Use 10000 for no limit.')),
                ('require_student', models.BooleanField(default=False)),
                ('publicly_visible', models.BooleanField(default=True, help_text=b'Can everyone see the holders of this office.')),
                ('grant_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='officeholder',
            name='role',
            field=models.ForeignKey(to='groups.OfficerRole'),
        ),
        migrations.AddField(
            model_name='group',
            name='group_class',
            field=models.ForeignKey(to='groups.GroupClass'),
        ),
        migrations.AddField(
            model_name='group',
            name='group_funding',
            field=models.ForeignKey(blank=True, to='groups.GroupFunding', null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='group_status',
            field=models.ForeignKey(to='groups.GroupStatus'),
        ),
    ]
