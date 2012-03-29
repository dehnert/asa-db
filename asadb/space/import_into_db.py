#!/usr/bin/python
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

max_date = datetime.datetime.max
today = datetime.date.today()

def process_row(line):
    group_id = int(line['group_id'])
    if group_id < 0:
        print "Ignoring missing group: %s: %s" % (line['group'], line, )
        return
    the_space, created = space.models.Space.objects.get_or_create(
        number=line['office_number'],
        defaults=dict(merged_acl=bool(line['locker_number'])),
    )
    group = groups.models.Group.objects.get(id=group_id)
    try:
        assignment = space.models.SpaceAssignment.objects.get(group=group, space=the_space, locker_num=line['locker_number'], end__gte=today)
        assignment.end = max_date
    except space.models.SpaceAssignment.DoesNotExist:
        assignment = space.models.SpaceAssignment(
            group=group,
            space=the_space,
            start=today,
            end=max_date,
            locker_num=line['locker_number'],
        )
    assignment.save()

def process_spaces(reader):
    space.models.SpaceAssignment.objects.filter(end=max_date).update(end=today)
    for line in reader:
        process_row(line)

if __name__ == '__main__':
    reader = csv.DictReader(sys.stdin)
    process_spaces(reader)
