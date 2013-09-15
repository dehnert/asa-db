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

import collections
import datetime

from django.db import transaction

fields = [
    # Django field, in order matching the input fields
    'username',
    'mit_id',
    'first_name',
    'last_name',
    'account_class',
    'affiliation_basic',
    'affiliation_detailed',
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
    django_people = groups.models.AthenaMoiraAccount.objects.all()
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
    stat_people = collections.defaultdict(list)
    for django_person in django_people:
        stat_loops += 1
        if stat_loops % 100 == 0:
            transaction.commit()
            pass
        mutable = django_person.mutable
        if django_person.username in dcm_people:
            # great, they're still in the dump
            changed = False
            changes = []
            dcm_person = dcm_people[django_person.username]
            del dcm_people[django_person.username]

            # Check for changes: first fields, then deletions
            for key in fields:
                if django_person.__dict__[key] != dcm_person[key]:
                    changed = True
                    if key == 'mit_id':
                        changes.append((key, '[redacted]', '[redacted]', ))
                    else:
                        changes.append((key, django_person.__dict__[key], dcm_person[key]))
                    if mutable:
                        django_person.__dict__[key] = dcm_person[key]
            if django_person.del_date is not None:
                changed = True
                if mutable:
                    django_person.del_date = None
                    stat_undel += 1
                    changes.append(('[account]', '[deleted]', '[undeleted]', ))
                    stat_people['undel'].append((django_person.username, changes))

            if changed:
                stat_name = ''
                if mutable:
                    django_person.mod_date = datetime.date.today()
                    django_person.save()
                    stat_changed += 1
                    stat_name = 'changed'
                else:
                    stat_mut_ign += 1
                    stat_name = 'mut_ign'
                stat_people[stat_name].append((django_person.username, changes))
            else:
                stat_unchanged += 1

        else:
            # They're not in the dump
            if django_person.del_date is None:
                stat_name = ''
                if mutable:
                    django_person.del_date = datetime.date.today()
                    stat_del += 1
                    stat_name = 'del'
                    django_person.save()
                else:
                    stat_mut_ign += 1
                    stat_name = 'mut_ign'
                changes = [('account_class', django_person.account_class, '[deleted]')]
                stat_people[stat_name].append((django_person.username, changes))
            else:
                stat_pre_del += 1

    transaction.commit()

    # Import new people from the DCM
    for username, dcm_person in dcm_people.items():
        stat_loops += 1
        if stat_loops % 100 == 0:
            transaction.commit()
            pass
        django_person = groups.models.AthenaMoiraAccount()
        for key in fields:
            django_person.__dict__[key] = dcm_person[key]
        django_person.add_date = datetime.date.today()
        stat_add += 1
        changes = [('account_class', '[missing]', dcm_person['account_class'], )]
        stat_people['add'].append((django_person.username, changes))
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
    return stats, stat_people


if __name__ == '__main__':
    print "Phase 1 (DCM parsing): starting at %s" % (datetime.datetime.now(), )
    dcm_people = load_dcm(sys.stdin)
    print "Phase 1 (DCM parsing): complete at %s" % (datetime.datetime.now(), )
    print "Phase 2 (Django updating): starting at %s" % (datetime.datetime.now(), )
    stats, stat_people = load_people(dcm_people)
    print "Phase 2 (Django updating): complete at %s" % (datetime.datetime.now(), )
    print """
Loop iterations:    %(loops)6d
Initial in Django:  %(django_people)6d
People in DCM:      %(dcm_people)6d
Already Deleted:    %(pre_del)6d
Unchanged:          %(unchanged)6d
Changed:            %(changed)6d
Change ignored:     %(mut_ign)6d
Deleted:            %(del)6d
Undeleted:          %(undel)6d
Added:              %(add)6d
""" % stats

    for change_type, people in stat_people.items():
        for person, changes in people:
            print "%12s\t%12s\t%s" % (change_type, person, changes, )
        print ""
