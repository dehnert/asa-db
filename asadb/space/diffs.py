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

from django.core.mail import EmailMessage
from django.db import connection
from django.db.models import Q
from django.template import Context, Template
from django.template.loader import get_template

import groups.diffs
import groups.models
import space.models
import util.emails

role = {
    'office': groups.models.OfficerRole.objects.get(slug='office-access')
}

people_name = {} # username -> full name
people_id = {} # username -> MIT ID

all_spaces = {} # Space.pk -> Space

def bulk_fill_people(times):
    max_time = max(times)
    min_time = min(times)
    active_holders = groups.models.OfficeHolder.objects.filter(
        start_time__lte=max_time,
        end_time__gte=min_time,
        role__in=role.values(),
    )
    usernames = active_holders.values_list('person', flat=True,)
    people = groups.models.AthenaMoiraAccount.objects.filter(username__in=usernames)
    for person in people:
        people_name[person.username] = person.format()
        people_id[person.username] = person.mit_id

def fill_people(holder):
    if not holder.person in people_name:
        #print "Person %s not pre-cached" % (holder.person, )
        try:
            person = groups.models.AthenaMoiraAccount.objects.get(username=holder.person)
            people_name[holder.person] = person.format()
            people_id[holder.person] = person.mit_id
        except groups.models.AthenaMoiraAccount.DoesNotExist:
            people_name[holder.person] = "<%s>" % (holder.person, )
            people_id[holder.person] = None

class GroupInfo(object):
    def __init__(self, group, ):
        self.group = group
        self.offices = {}  # Space.pk -> (ID -> (Set name, Set name))
        if not role:
            role['office'] = groups.models.OfficerRole.objects.get(slug='office-access')

    def learn_access(self, space_pk, old, new):
        group_pk = self.group.pk
        if group_pk in old:
            old_access = old[group_pk]
        else: old_access = {}
        if group_pk in new:
            new_access = new[group_pk]
        else: new_access = {}
        assert space_pk not in self.offices

        # Let's fill out the self.offices set.
        self.offices[space_pk] = collections.defaultdict(lambda: (set(), set()))
        space_data = self.offices[space_pk]
        for mit_id, old_set in old_access.items():
            space_data[mit_id][0].update(old_set)
        for mit_id, new_set in new_access.items():
            space_data[mit_id][1].update(new_set)

    def add_office_signatories_per_time(self, ind, time):
        group = self.group
        people = group.officers(as_of=time, role=role['office'])
        for holder in people:
            fill_people(holder)
        for office_id, office_data in self.offices.items():
            for holder in people:
                holder_name = people_name[holder.person]
                holder_id = people_id[holder.person]
                office_data[holder_id][ind].add(holder_name)

    def add_office_signatories(self, old_time, new_time, ):
        group = self.group
        self.add_office_signatories_per_time(0, old_time)
        self.add_office_signatories_per_time(1, new_time)

    def list_changes(self, ):
        cac_lines = []
        group_lines = []
        def append_change(mit_id, verb, name):
            cac_lines.append("%s:\t%s:\t%s" % (mit_id, verb, name))
            group_lines.append("%s:\t%s" % (verb, name))
        changes = False
        for space_pk, space_data in self.offices.items():
            line = "Changes in %s:" % (all_spaces[space_pk].number, )
            cac_lines.append(line)
            group_lines.append(line)
            for mit_id, (old_names, new_names) in space_data.items():
                if mit_id is None: mit_id = "ID unknown"
                if old_names == new_names:
                    pass
                else:
                    changes = True
                    for name in old_names:
                        if name in new_names:
                            append_change(mit_id, "Keep", name)
                        else:
                            append_change(mit_id, "Remove", name)
                    for name in new_names:
                        if name in old_names:
                            pass
                        else:
                            append_change(mit_id, "Add", name)
            cac_lines.append("")
            group_lines.append("")

        cac_msg = "\n".join(cac_lines)
        group_msg = "\n".join(group_lines)
        return changes, cac_msg, group_msg

def init_groups(the_groups, assignments):
    for assignment in assignments:
        group = assignment.group
        if group.id not in the_groups:
            the_groups[group.id] = GroupInfo(group)

def space_specific_access(group_data, old_time, new_time, ):
    process_spaces =  space.models.Space.objects.all()
    #process_spaces = process_spaces.filter(number="W20-467")
    for the_space in process_spaces:
        old_data = the_space.build_access(time=old_time)
        new_data = the_space.build_access(time=new_time)
        all_spaces[the_space.pk] = the_space
        init_groups(group_data, old_data[2])
        init_groups(group_data, new_data[2])
        for group_pk, group in group_data.items():
            if group_pk in old_data[0] or group_pk in new_data[0]:
                group.learn_access(the_space.pk, old_data[0], new_data[0])


def space_access_diffs():
    new_time = datetime.datetime.utcnow()
    old_time = new_time - datetime.timedelta(days=1)
    bulk_fill_people([old_time, new_time])
    group_data = {} # Group.pk -> GroupInfo
    changed_groups = []
    space_specific_access(group_data, old_time, new_time)
    for group_pk, group_info in group_data.items():
        group_info.add_office_signatories(old_time, new_time)
        changes, cac_changes, group_changes = group_info.list_changes()
        if changes:
            changed_groups.append((group_info.group, cac_changes, group_changes))

    asa_rcpts = ['asa-space@mit.edu', 'asa-db@mit.edu', ]
    util.emails.email_from_template(
        tmpl='space/cac-change-email.txt',
        context={'changed_groups': changed_groups},
        subject="Office access updates",
        to=['caclocks@mit.edu'],
        cc=asa_rcpts,
    ).send()
    for group, cac_msg, group_msg in changed_groups:
        util.emails.email_from_template(
            tmpl='space/group-change-email.txt',
            context={
                'group':group,
                'msg':group_msg,
            },
            subject="Office access updates",
            to=[group.officer_email],
            cc=asa_rcpts,
        ).send()
        

if __name__ == "__main__":
    space_access_diffs()
