#!/usr/bin/python
#
# Exports data for the Finboard app as JSON: currently just group
# id/name/account number and P/T/GA/FS
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
    gs = groups.models.Group.objects.filter(group_status__is_active=True)
    gs = gs.filter(group_funding__slug='undergrad')

    officers = groups.models.OfficeHolder.current_holders
    officers = officers.filter(group__in=gs, role__slug__in=ROLES)
    officers = officers.select_related('role__slug', 'group')

    group_dicts = {}
    for group in gs:
        group_dict = {
            'id': group.id,
            'name': group.name,
            'funding-account': group.funding_account_id,
        }
        for role in ROLES:
            group_dict[role] = []
        group_dicts[group.id] = group_dict

    for officer in officers:
        group_dicts[officer.group.id][officer.role.slug].append(officer.person)

    out = codecs.getwriter('utf-8')(sys.stdout)
    json.dump({
        'groups': group_dicts.values(),
        'date': datetime.datetime.now().isoformat(),
    }, out, indent=2)
