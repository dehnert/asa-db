#!/usr/bin/python
#
# Exports data for the Finboard app as JSON: currently just group id/name and
# P/T/GA/FS
#
# Use as e.g.
# ./export_finboard_groups.py > /mit/asa-db/data/finboard/groups.json

import codecs
import datetime
import json
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models

ROLES = ['president', 'treasurer', 'financial', 'group-admin']

if __name__ == '__main__':
    groups = groups.models.Group.objects.filter(group_status__is_active=True)
    groups = groups.filter(group_funding__slug='undergrad')
    groups = groups.filter(officeholder__role__slug__in=ROLES)
    groups.prefetch_related('officeholder_set', 'officeholder_set__officerrole')
    groups = groups.distinct()

    group_dicts = []
    for group in groups:
        # do the processing in python because of the prefetch_related
        officers = list(group.officeholder_set.all())
        group_dict = {
            'id': group.id,
            'name': group.name,
        }
        for role in ROLES:
            group_dict[role] = [officer.person for officer in officers
                                if officer.role.slug == role]
        group_dicts.append(group_dict)

    out = codecs.getwriter('utf-8')(sys.stdout)
    json.dump({
        'groups': group_dicts,
        'date': datetime.datetime.now().isoformat(),
    }, out)
