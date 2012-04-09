#!/usr/bin/python
import collections
import csv
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

def print_info(space_users, stream=None, ):
    if not stream: stream = sys.stdout
    writer = csv.writer(stream)
    writer.writerow(("space", "last_name", "first_name", "username", "mit_id", ))
    for space_id, users in space_users.items():
        writer.writerow(())
        cur_space = space.models.Space.objects.get(pk=space_id)
        writer.writerow((cur_space, ))
        user_objs = groups.models.AthenaMoiraAccount.objects.filter(username__in=users).order_by('last_name', 'first_name', )
        for user in user_objs:
            writer.writerow((cur_space, user.last_name, user.first_name, user.username, user.mit_id))

if __name__ == '__main__':
    space_users = gather_users()
    print_info(space_users)
