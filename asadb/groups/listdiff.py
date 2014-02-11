#!/usr/bin/python

import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db import connection

import groups.models
import util.mailinglist

def get_lists():
    status_objs = groups.models.GroupStatus.objects.filter(slug__in=['active', 'suspended', ])
    active_groups = groups.models.Group.objects.filter(group_status__in=status_objs)
    funded_groups = active_groups.filter(group_class__slug='mit-funded')
    return (
        #(
        #    util.mailinglist.MoiraList('finboard-groups-only'),
        #    funded_groups.filter(group_funding__slug='undergrad'),
        #),
        #(
        #    util.mailinglist.MailmanList('gsc-fb-'),
        #    funded_groups.filter(group_funding__slug='grad'),
        #),
        (
            util.mailinglist.MailmanList('asa-official'),
            active_groups,
            'asa-official-listeners@mit.edu',
        ),
    )

def diff_lists(lists):
    for lst, group_filter, listeners in lists:
        list_addresses = set(email.lower() for email in lst.list_members())
        db_addresses = set()
        if listeners:
            db_addresses.add(listeners)
        for group in group_filter:
            email = group.officer_email.lower()
            db_addresses.add(email)
            if email not in list_addresses:
                print "%24s:\t%s:\t%s (%s)" % (lst.name, 'miss', email, group.name, )
        print ""
        for email in list_addresses-db_addresses:
            print "%24s:\t%s:\t%s" % (lst.name, 'extra', email, )
        print ""

        print "%24s: contains %d (list) vs. %d/%d (DB); %d missing from list; %d extra on list" % (
            lst.name,
            len(list_addresses),
            len(db_addresses), # this includes only one blank email,
            len(group_filter), # so may be much lower than this one
            len(db_addresses-list_addresses),
            len(list_addresses-db_addresses),
        )
        print ""

if __name__ == '__main__':
    diff_lists(get_lists())
