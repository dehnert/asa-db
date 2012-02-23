#!/usr/bin/python
import collections
import datetime
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models
import space.models

def gather_users():
    spaces_groups = collections.defaultdict(set)
    spaces_list = space.models.SpaceAssignment.current.filter()
    for assignment in spaces_list:
        if assignment.is_locker():
            spaces_groups[assignment.space.pk].add(assignment.group)
    space_users = {}
    role = groups.models.OfficerRole.objects.get(slug='locker-access')
    for space_id, space_groups in spaces_groups.items():
        users = set()
        for group in space_groups:
            holders = group.officers(role=role)
            for holder in holders: users.add(holder.person)
        space_users[space_id] = users
    return space_users

def print_info(space_users):
    for space_id, users in space_users.items():
        print "\n\n%s:" % (space.models.Space.objects.get(pk=space_id), )
        user_objs = groups.models.AthenaMoiraAccount.objects.filter(username__in=users)
        for user in user_objs:
            print "%s (%s %s, %s)" % (user.username, user.first_name, user.last_name, user.mit_id)

if __name__ == '__main__':
    space_users = gather_users()
    print_info(space_users)
