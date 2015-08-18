# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FYSM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(help_text=b'Form of your name suitable for display (for example, don\'t end your name with ", MIT")', max_length=50)),
                ('year', models.IntegerField(db_index=True)),
                ('website', models.URLField()),
                ('join_url', models.URLField(help_text=b'<p>If you have a specific web page for recruiting new members of your group, you can link to it here. It will be used as the destination for most links about your group (join link on the main listing page and when clicking on the slide, but not the "website" link on the slide page). If you do not have such a page, use your main website\'s URL.</p>', verbose_name=b'recruiting URL')),
                ('contact_email', models.EmailField(help_text=b'Give an address for students interested in joining the group to email (e.g., an officers list)', max_length=254)),
                ('description', models.TextField(help_text=b'Explain, in no more than 400 characters (including spaces), what your group does and why incoming students should get involved.')),
                ('logo', models.ImageField(help_text=b'Upload a logo (JPG, GIF, or PNG) to display on the main FYSM page as well as the group detail page. This will be scaled to be 100px wide.', upload_to=b'fysm/logos', blank=True)),
                ('slide', models.ImageField(default=b'', help_text=b'Upload a slide (JPG, GIF, or PNG) to display on the group detail page. This will be scaled to be at most 600x600 pixels. We recommend making it exactly that size.', upload_to=b'fysm/slides', blank=True)),
                ('tags', models.CharField(help_text=b'Specify some free-form, comma-delimited tags for your group', max_length=100, blank=True)),
            ],
            options={
                'verbose_name': 'FYSM submission',
            },
        ),
        migrations.CreateModel(
            name='FYSMCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=25)),
                ('slug', models.SlugField(unique=True)),
                ('blurb', models.TextField()),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'FYSM category',
                'verbose_name_plural': 'FYSM categories',
            },
        ),
        migrations.CreateModel(
            name='FYSMView',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('when', models.DateTimeField(default=datetime.datetime.now)),
                ('year', models.IntegerField(null=True, blank=True)),
                ('page', models.CharField(max_length=20, blank=True)),
                ('referer', models.URLField(null=True)),
                ('user_agent', models.CharField(max_length=255)),
                ('source_ip', models.IPAddressField()),
                ('source_user', models.CharField(max_length=30, blank=True)),
                ('fysm', models.ForeignKey(blank=True, to='forms.FYSM', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupConfirmationCycle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('slug', models.SlugField(unique=True)),
                ('create_date', models.DateTimeField(default=datetime.datetime.now)),
                ('deadlines', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupMembershipUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_time', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
                ('updater_name', models.CharField(max_length=30)),
                ('updater_title', models.CharField(help_text=b'You need not hold any particular title in the group, but we like to know who is completing the form.', max_length=30)),
                ('group_email', models.EmailField(help_text=b'The text of the law will be automatically distributed to your members via this list, in order to comply with the law.', max_length=254)),
                ('officer_email', models.EmailField(max_length=254)),
                ('membership_definition', models.TextField()),
                ('num_undergrads', models.IntegerField()),
                ('num_grads', models.IntegerField()),
                ('num_alum', models.IntegerField()),
                ('num_other_affiliate', models.IntegerField(verbose_name=b'Num other MIT affiliates')),
                ('num_other', models.IntegerField(verbose_name=b'Num non-MIT')),
                ('membership_list', models.TextField(help_text=b'Member emails on separate lines (Athena usernames where applicable)', blank=True)),
                ('email_preface', models.TextField(help_text=b'If you would like, you may add text here that will preface the text of the policies when it is sent out to the group membership list provided above.', blank=True)),
                ('no_hazing', models.BooleanField(default=False, help_text=b"By checking this, I hereby affirm that I have read and understand <a href='http://web.mit.edu/asa/rules/ma-hazing-law.html'>Chapter 269: Sections 17, 18, and 19 of Massachusetts Law</a>. I furthermore attest that I have provided the appropriate address or will otherwise distribute to group members, pledges, and/or applicants, copies of Massachusetts Law 269: 17, 18, 19 and that our organization, group, or team agrees to comply with the provisions of that law. (See below for text.)")),
                ('no_discrimination', models.BooleanField(default=False, help_text=b"By checking this, I hereby affirm that I have read and understand the <a href='http://web.mit.edu/referencepubs/nondiscrimination/'>MIT Non-Discrimination Policy</a>.  I furthermore attest that our organization, group, or team agrees to not discriminate against individuals on the basis of race, color, sex, sexual orientation, gender identity, religion, disability, age, genetic information, veteran status, ancestry, or national or ethnic origin.")),
                ('cycle', models.ForeignKey(to='forms.GroupConfirmationCycle')),
                ('group', models.ForeignKey(help_text=b'If your group does not appear in the list above, then please email asa-exec@mit.edu.', to='groups.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Midway',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField()),
                ('date', models.DateTimeField()),
                ('table_map', models.ImageField(upload_to=b'midway/maps')),
            ],
        ),
        migrations.CreateModel(
            name='MidwayAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', models.CharField(max_length=20)),
                ('group', models.ForeignKey(to='groups.Group')),
                ('midway', models.ForeignKey(to='forms.Midway')),
            ],
        ),
        migrations.CreateModel(
            name='PagePreview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_time', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
                ('url', models.URLField()),
                ('image', models.ImageField(upload_to=b'page-previews', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PeopleStatusLookup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('people', models.TextField(help_text=b'Enter some usernames or email addresses, separated by newlines, to look up here.')),
                ('referer', models.URLField(blank=True)),
                ('time', models.DateTimeField(default=datetime.datetime.now)),
                ('classified_people_json', models.TextField()),
                ('requestor', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PersonMembershipUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_time', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0))),
                ('username', models.CharField(max_length=30)),
                ('deleted', models.DateTimeField(default=None, null=True, blank=True)),
                ('valid', models.IntegerField(default=0, choices=[(0, b'unvalidated'), (10, b'autovalidated'), (20, b'hand-validated'), (-10, b'autorejected'), (-20, b'hand-rejected')])),
                ('cycle', models.ForeignKey(to='forms.GroupConfirmationCycle')),
                ('groups', models.ManyToManyField(help_text=b'By selecting a group here, you indicate that you are an active member of the group in question.<br>If your group does not appear in the list above, then please email asa-exec@mit.edu.<br>', to='groups.Group')),
            ],
        ),
        migrations.AddField(
            model_name='fysm',
            name='categories',
            field=models.ManyToManyField(help_text=b'Put your group into whichever of our categories seem applicable.', to='forms.FYSMCategory', blank=True),
        ),
        migrations.AddField(
            model_name='fysm',
            name='group',
            field=models.ForeignKey(to='groups.Group'),
        ),
        migrations.AddField(
            model_name='fysm',
            name='join_preview',
            field=models.ForeignKey(to='forms.PagePreview', null=True),
        ),
    ]
