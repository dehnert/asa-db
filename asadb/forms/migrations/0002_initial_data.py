# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

fysm_cats = [
    dict(
        name='Academic',
        slug='academic',
        blurb="""Academic groups include departmental groups, MIT chapters of 
national academic societies, teams for academic competitions, 
pre-professional groups, and ethnic academic groups.  These
groups have a wide-range of activities from study breaks and
formals to tutoring and academic support programs."""
    ),
    dict(
        name='Activism',
        slug='activism',
        blurb="""MIT has a wide range of social, political, economic, and environmental 
activism groups.  These groups span the political spectrum and hold 
events from small discussions to large public forums."""
    ),
    dict(
        name='Arts',
        slug='arts',
        blurb="""MIT's artistic groups include, but are not limited to: 
performance ensembles, theater troupes, vocal ensembles, 
dance groups, instrumental music organizations, and visual 
art societies.  Even though practically all MIT students 
are not at MIT to study their art, many find time to take 
part in one of the more than 40 artistic student activities.  
In addition to the many social groups, MIT's performance 
ensembles put on more than 25 shows and concerts every 
semester ranging from classical music to modern dance to 
theater to comedy."""
    ),
    dict(
        name='Athletic',
        slug='athletic',
        blurb="""In addition to its many varsity sports, MIT has a wide 
range of club sports and other athletic groups.  The 
Club Sports Council (also a student group) oversees more 
than 30 teams that are student-organized including both 
competitive teams and more instructional activities.  
Beyond club sports, there are many less formal or less 
traditional athletic groups."""
    ),
    dict(
        name='Campus Media',
        slug='media',
        blurb="""Campus Media groups produce various publications with content 
created by students. This includes the newspaper, radio, 
television programs, the yearbook, a guide to MIT, and art 
magazine, among others. """
    ),
    dict(
        name='Cultural',
        slug='cultural',
        blurb="""MIT students come from all over the world, and the more 
than 60 student cultural groups reflect their diverse 
backgrounds.  Most of these organizations are social in 
nature, but there are also many language and traditional 
dance and music groups.  A lot of these groups hold large
campus-wide events every year, celebrating their cultures
and sharing them with the rest of campus."""
    ),
    dict(
        name='Interest',
        slug='interest',
        blurb="""There is no simple way to summarize all the special interest 
activities at MIT.  They span such an impressively wide range 
of topics and there are new groups starting every semester.  
There are business competitions, clubs all about a specific 
food, gaming societies, and many more."""
    ),
    dict(
        name='Recreational',
        slug='recreational',
        blurb="""Recreational groups include many of the fun, random activities that 
MIT students are involved in.  There are groups for all kinds of
things from Rubik's cubes to outdoor excursions to dancing.  In 
addition to the many groups in existence, students are forming
new organization every semester."""
    ),
    dict(
        name='Religious',
        slug='religious',
        blurb='The more than 30 religious groups at MIT represent a wide range of belief systems and practices.  They have all kinds of activites from regular prayer services to community dinners and holiday celebrations to scripture study.'
    ),
    dict(
        name='Service',
        slug='service',
        blurb="""MIT has more than 30 service groups that take on projects 
and initiatives on campus, in the local Cambridge/Boston 
region, and all around the country and world.  As a part
of these groups, MIT students use their skills and expertise
on topics ranging from medical or educational intiatives to
international development projects."""
    ),
    dict(
        name='Student Government',
        slug='government',
        blurb="""MIT's student governments advocate on behalf of students to the 
MIT Administration. They also plan campus-wide events, organize 
student activities and living groups, and accomplish much more.  
In general, student government at MIT is highly autonomous from 
the MIT Administration and quite influential in terms of student 
life and other student interests."""
    ),
    dict(
        name='Technology',
        slug='technology',
        blurb="""Given that we are an institute of technology, we have 
a category just for technology groups.  These groups 
discuss technology, practice forms of technology, and 
design and implement new technologies."""
    ),
]

def create_fysmcats(apps, db_alias):
    FYSMCat = apps.get_model('forms', 'FYSMCategory')
    cats = [FYSMCat(**kwargs) for kwargs in fysm_cats]
    FYSMCat.objects.using(db_alias).bulk_create(cats)

def create_initial_data(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    create_fysmcats(apps, db_alias)

class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
