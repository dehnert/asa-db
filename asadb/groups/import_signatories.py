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
from django.db import transaction


def dictize_line(header, line,):
    line_dict = {}
    for key, elem in zip(header, line, ):
        line_dict[key]=elem
    return line_dict

def db_parse_date(string, allow_none=False):
    if not string:
        return None
    else:
        return datetime.datetime.strptime(string, '%d-%b-%y').date()

def load_django(stats, ):
    zero_time = datetime.time()
    office_holders = groups.models.OfficeHolder.current_holders.all()
    dj_map = collections.defaultdict(lambda: None)
    for office_holder in office_holders:
        if office_holder.start_time.time() == zero_time:
            key = (office_holder.person, office_holder.role.slug, office_holder.group.pk)
            dj_map[key] = office_holder
    stats['dj_total_current'] = len(office_holders)
    stats['dj_distinct_current'] = len(office_holders)
    return dj_map

def load_warehouse(stats, ):
    indb = sys.stdin
    reader = csv.reader(indb)
    header = reader.next()
    wh_map = collections.defaultdict(set)
    stats['wh_entries'] = 0
    for line in reader:
        d = dictize_line(header, line)
        role_slug = d['ASA_OFFICER_ROLE_KEY'].lower()
        person = d['KERBEROS_NAME']
        group_id = int(d['ASA_STUDENT_GROUP_KEY'])
        start = db_parse_date(d['EFFECTIVE_DATE'], True)
        expiry = db_parse_date(d['EXPIRATION_DATE'], True)
        key = (person, role_slug, group_id, )
        wh_map[key].add((start, expiry, ))
        stats['wh_entries'] += 1
    stats['wh_size'] = len(wh_map)
    return wh_map

def load_roles():
    all_roles = groups.models.OfficerRole.objects.all()
    role_map = {}
    for role in all_roles:
        role_map[role.slug] = role
    return role_map

def load_groups():
    all_groups = groups.models.Group.objects.all()
    group_map = {}
    for group in all_groups:
        group_map[group.pk] = group
    return group_map

@transaction.commit_on_success
def perform_sync(stats, dj_map, wh_map, ):
    # Statistics
    stats['loops'] = 0
    stats['postdate_start'] = 0
    stats['kept'] = 0
    stats['expired'] = 0
    stats['missing_wh'] = 0
    stats['added'] = 0
    stats['missing_rg'] = 0

    today = datetime.date.today()
    roles = load_roles()
    dj_groups = load_groups()
    for key in set(dj_map.keys()).union(wh_map.keys()):
        stats['loops'] += 1
        if stats['loops'] % 1000 == 0:
            print "Sync: at loop %d" % (stats['loops'], )
        dj_holder = dj_map[key]
        wh_times = wh_map[key]
        person, role_slug, group_id = key
        if dj_holder:
            if len(wh_times) > 0:
                found_current = False
                for start, expiry in wh_times:
                    if start > today: # people *actually* post-date effective dates?
                        stats['postdate_start'] += 1
                    elif expiry is None:
                        found_current = True
                    elif expiry >= today:
                        found_current = True
                    else: # already expired
                        pass
                if found_current:
                    stats['kept'] += 1
                else:
                    # expire it
                    dj_holder.expire()
                    stats['expired'] += 1
            else:
                # Weird. This person doesn't appear in Warehouse
                stats['missing_wh'] += 1
        else:
            for start, expiry in wh_times:
                if start <= today and (expiry is None or expiry > today):
                    if group_id in dj_groups and role_slug in roles:
                        # New signatory
                        role = roles[role_slug]
                        group = dj_groups[group_id]
                        if expiry is None: expiry = groups.models.OfficeHolder.END_NEVER
                        dj_holder = groups.models.OfficeHolder(
                            person=person, role=role, group=group,
                            start_time=start, end_time=expiry
                        )
                        dj_holder.save()
                        stats['added'] += 1
                    else:
                        print "Missing role or group: person=%s, role=%s, group=%d, start=%s, expiry=%s" % (
                            person, role_slug, group_id, start, expiry,
                        )
                        stats['missing_rg'] += 1

if __name__ == '__main__':
    stats = {}

    print "Phase 1: %s: Loading Django officer information" % (datetime.datetime.now(), )
    dj_map = load_django(stats)
    print "Phase 1: %s: Complete: Loading Django officer information" % (datetime.datetime.now(), )

    print "Phase 2: %s: Loading warehouse officer information" % (datetime.datetime.now(), )
    wh_map = load_warehouse(stats)
    print "Phase 2: %s: Complete: Loading warehouse officer information" % (datetime.datetime.now(), )

    print "Phase 3: %s: Performing sync" % (datetime.datetime.now(), )
    perform_sync(stats, dj_map, wh_map, )
    print "Phase 3: %s: Complete: Performing sync" % (datetime.datetime.now(), )

    print """
    All phases complete. Statistics:
    
    Django current:         %(dj_total_current)6d
    Django distinct:        %(dj_distinct_current)6d

    Warehouse p/r/g tuples: %(wh_size)6d
    Warehouse entries:      %(wh_entries)6d

    Time around sync loop:  %(loops)6d
    Postdated start date:   %(postdate_start)6d
    People kept:            %(kept)6d
    People expired:         %(expired)6d
    People missing from WH: %(missing_wh)6d
    People added:           %(added)6d
    """ % stats
