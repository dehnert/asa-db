#!/usr/bin/python

import sys
import os

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    proj_dir = os.path.abspath(os.path.join(django_dir, '..'))
    sys.path.append(django_dir)
    sys.path.append(proj_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models

import datetime

from django.db import transaction

fields = [
    # Django field, in order matching the input fields
    'username',
    'mit_id',
    'first_name',
    'last_name',
    'account_class',
]

def load_dcm(dcm_stream):
    dcm_people = {}
    for line in dcm_stream:
        line = line.strip()
        field_list = line.split("\t")
        field_dict = {}
        for index, field in enumerate(fields):
            field_dict[field] = field_list[index]
        dcm_people[field_dict['username']] = field_dict
    return dcm_people

@transaction.commit_manually
def load_people(dcm_people):
    django_people = groups.models.AthenaMoiraPerson.objects.all()
    stat_loops = 0
    stat_django_people = len(django_people)
    stat_dcm_people = len(dcm_people)
    stat_changed = 0
    stat_mut_ign = 0
    stat_unchanged = 0
    stat_del = 0
    stat_pre_del = 0
    stat_undel = 0
    stat_add = 0
    for django_person in django_people:
        stat_loops += 1
        if stat_loops % 100 == 0:
            transaction.commit()
            pass
        mutable = django_person.mutable
        if django_person.username in dcm_people:
            # great, they're still in the dump
            changed = False
            dcm_person = dcm_people[django_person.username]
            del dcm_people[django_person.username]
            for key in fields:
                if django_person.__dict__[key] != dcm_person[key]:
                    changed = True
                    if mutable:
                        django_person.__dict__[key] = dcm_person[key]
            if django_person.del_date is not None:
                changed = True
                if mutable:
                    django_person.del_date = None
                    stat_undel += 1
            if changed:
                if mutable:
                    django_person.mod_date = datetime.date.today()
                    django_person.save()
                    stat_changed += 1
                else:
                    stat_mut_ign += 1
            else:
                stat_unchanged += 1
        else:
            if django_person.del_date is None:
                if mutable:
                    django_person.del_date = datetime.date.today()
                    stat_del += 1
                    django_person.save()
                else:
                    stat_mut_ign += 1
            else:
                stat_pre_del += 1
    for username, dcm_person in dcm_people.items():
        stat_loops += 1
        if stat_loops % 100 == 0:
            transaction.commit()
            pass
        django_person = groups.models.AthenaMoiraPerson()
        for key in fields:
            django_person.__dict__[key] = dcm_person[key]
        django_person.add_date = datetime.date.today()
        stat_add += 1
        django_person.save()
    transaction.commit()
    stats = {
        'loops': stat_loops,
        'django_people': stat_django_people,
        'dcm_people': stat_dcm_people,
        'changed': stat_changed,
        'mut_ign': stat_mut_ign,
        'unchanged': stat_unchanged,
        'del': stat_del,
        'pre_del': stat_pre_del,
        'undel': stat_undel,
        'add': stat_add,
    }
    return stats


if __name__ == '__main__':
    print "Phase 1 (DCM parsing): starting at %s" % (datetime.datetime.now(), )
    dcm_people = load_dcm(sys.stdin)
    print "Phase 1 (DCM parsing): complete at %s" % (datetime.datetime.now(), )
    print "Phase 2 (Django updating): starting at %s" % (datetime.datetime.now(), )
    stats = load_people(dcm_people)
    print "Phase 2 (Django updating): complete at %s" % (datetime.datetime.now(), )
    print """
Loop iterations:    %(loops)6d
Initial in Django:  %(django_people)6d
People in DCM:      %(dcm_people)6d
Changed:            %(changed)6d
Change ignored:     %(mut_ign)6d
Unchanged:          %(unchanged)6d
Deleted:            %(del)6d
Already Deleted:    %(pre_del)6d
Undeleted:          %(undel)6d
Added:              %(add)6d""" % stats
