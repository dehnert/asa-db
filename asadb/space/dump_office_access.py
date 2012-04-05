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

def current_groups():
    return space.models.SpaceAssignment.current.values_list('group', flat=True)

def people_lookup():
    office_access = groups.models.OfficeHolder.current_holders.filter(role__slug='office-access', group__in=current_groups()).values_list('person', flat=True)
    current_users = groups.models.AthenaMoiraAccount.objects.filter(username__in=office_access)
    user_map = {}
    for user in current_users:
        user_map[user.username] = user
    return user_map

def space_lookup():
    space_list = space.models.Space.objects.all()
    space_map = {}
    for space_obj in space_list:
        space_map[space_obj.pk] = space_obj
    return space_map

def group_lookup():
    group_list = groups.models.Group.objects.filter(id__in=current_groups())
    group_map = {}
    for group_obj in group_list:
        group_map[group_obj.pk] = group_obj
    return group_map

def gather_users():
    spaces_list = space.models.SpaceAssignment.current.filter()
    space_aces = collections.defaultdict(dict)
    for assignment in spaces_list:
        if not assignment.is_locker():
            space_aces[assignment.space_id][assignment.group_id] = set()
    for ace in space.models.SpaceAccessListEntry.current.filter(group__in=current_groups()):
        if ace.group_id in space_aces[ace.space_id]:
            space_aces[ace.space_id][ace.group_id].add(ace)
    return space_aces


    holders = groups.models.OfficerRole.current_holders.filter(role__slug='office-access')

def print_info():
    people_map = people_lookup()
    space_map = space_lookup()
    group_map = group_lookup()

    # Load office-access folks
    group_holders = collections.defaultdict(set)
    for holder in groups.models.OfficeHolder.current_holders.filter(role__slug='office-access', group__in=current_groups()):
        group_holders[holder.group_id].add((holder, people_map[holder.person]))

    # Load room-specific stuff
    space_aces = gather_users()

    writer = csv.writer(sys.stdout)
    writer.writerow(("space", "group", "last_name", "first_name", "username", "mit_id", ))
    for space_id, space_groups in space_aces.items():
        space_obj = space_map[space_id]
        writer.writerow(())
        for group_id, aces in space_groups.items():
            group_obj = group_map[group_id]
            writer.writerow(())
            for ace in aces:
                writer.writerow((space_obj, group_obj, "", ace.name, "", ace.card_number, ))
            for holder, person in group_holders[group_id]:
                writer.writerow((space_obj, group_obj, person.last_name, person.first_name, person.mit_id, ))

if __name__ == '__main__':
    print_info()
