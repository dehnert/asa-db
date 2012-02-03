#!/usr/bin/python
import csv
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models

def process_spaces(in_spaces, out_spaces):
    offices = set()
    lockers = set()
    for line in in_spaces:
        space = line['space']
        locker_number = ""
        if space.count("-") > 1:
            res = space.rsplit("-", 1)
            office_number, locker_number = res
            lockers.add(office_number)
        else:
            office_number = space
            offices.add(office_number)
        if space.count(","):
            office_number = "???"

        group_name = line['group']
        found_name = ""
        try:
            group = groups.models.Group.objects.get(name__startswith=group_name)
            #group = groups.models.Group.objects.get(name=group_name)
            group_id = group.pk
            found_name = group.name
        except groups.models.Group.MultipleObjectsReturned:
            group_id = -2
        except groups.models.Group.DoesNotExist:
            group_id = -1

        out_spaces.writerow((space, group_name, found_name, group_id, office_number, locker_number, ))
    
    print >>sys.stderr, "lockers=%s;   offices=%s;    both=%s" % (lockers, sorted(offices), lockers & offices, )
        
if __name__ == '__main__':
    reader = csv.DictReader(sys.stdin)
    writer = csv.writer(sys.stdout)
    writer.writerow(("space", "group", "found_name", "group_id", "office_number", "locker_number", ))
    process_spaces(reader, writer)
