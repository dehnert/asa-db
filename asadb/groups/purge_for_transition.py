#!/usr/bin/python
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models
from django.db import transaction
from django.db.models import Q

def clean_group(group):
    group.activity_category = None
    group.description = ""

    group.num_undergrads = None
    group.num_grads = None
    group.num_community = None
    group.num_other = None

    group.website_url = ""
    group.meeting_times = ""
    group.officer_email = ""
    group.group_email = ""

    group.constitution_url = ""
    group.advisor_name = ""
    group.athena_locker = ""

    officers = group.officers().filter(~Q(role__slug='president'))
    for officer in officers: officer.expire()

    group.set_updater("importer@SYSTEM")
    group.save()


@transaction.commit_on_success
def clean_groups():
    for group in groups.models.Group.active_groups.all():
        clean_group(group)

if __name__ == '__main__':
    clean_groups()
