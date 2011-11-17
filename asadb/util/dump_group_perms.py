#!/usr/bin/python
import os
import pprint
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.contrib.auth.models

def perm_tuple(perm):
    return (perm.content_type.app_label, perm.content_type.model, perm.codename)

def dump_group_perms():
    groups = []
    for group in django.contrib.auth.models.Group.objects.all():
        groups.append((group.name, [
            perm_tuple(perm) for perm in group.permissions.all()
        ]))
    return groups

if __name__ == '__main__':
    pprint.pprint(dump_group_perms())
