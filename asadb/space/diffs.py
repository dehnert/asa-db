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
    'office': groups.models.OfficerRole.objects.get(slug='office-access'),
    'locker': groups.models.OfficerRole.objects.get(slug='locker-access'),
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
        self.locker_acl = {}
        self.locker_messages = []
        self.changes = False

    def learn_office_access(self, space_pk, old, new):
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

    def list_office_changes(self, ):
        cac_lines = []
        group_lines = []
        def append_change(mit_id, verb, name):
            cac_lines.append("%s:\t%s:\t%s" % (mit_id, verb, name))
            group_lines.append("%s:\t%s" % (verb, name))
        for space_pk, space_data in self.offices.items():
            line = "Changes in %s:" % (all_spaces[space_pk].number, )
            cac_lines.append(line)
            group_lines.append(line)
            for mit_id, (old_names, new_names) in space_data.items():
                if mit_id is None: mit_id = "ID unknown"
                if old_names == new_names:
                    pass
                else:
                    self.changes = True
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
        return cac_msg, group_msg

    def add_locker_signatories(self, space_access, time):
        # space_access: ID -> (Name -> (Set Group.pk))
        if time in self.locker_acl:
            locker_acl = self.locker_acl[time]
        else:
            locker_acl = self.group.officers(as_of=time, role=role['locker'])
            self.locker_acl[time] = locker_acl
        for holder in locker_acl:
            fill_people(holder)
            holder_name = people_name[holder.person]
            holder_id = people_id[holder.person]
            space_access[holder_id][holder_name].add(self.group.pk)

def init_groups(the_groups, assignments):
    for assignment in assignments:
        group = assignment.group
        if group.id not in the_groups:
            the_groups[group.id] = GroupInfo(group)

def flip_dict(dct):
    new = collections.defaultdict(set)
    for key, vals in dct.items():
        for val in vals:
            new[val].add(key)
    return new

def joint_keys(dct1, dct2):
    return set(dct1.keys()).union(dct2.keys())

class LockerAccessChangeEntry(object):
    def __init__(self, mit_id, verb, name, groups):
        self.mit_id = mit_id
        self.verb = verb
        self.name = name
        self.cac_msgs = ""
        self.group_msgs = ""
        self.groups = groups

    def cac_format(self):
        return "%s\t%s\t%s\t%s" % (self.mit_id, self.verb, self.name, self.cac_msgs)

    def group_format(self):
        return "%s\t%s\t%s" % (self.verb, self.name, self.group_msgs)

def safe_add_change_real(change_by_name, change):
    """Add a new change to our dict of pending changes.

    If a different change has already been added for this person (eg, "Remove"
    instead of "Keep", or with a different list of groups), error.  This should
    always succeed; if it doesn't, the code is buggy. We worry about this
    because we want to be really sure that the email that goes to just CAC is
    compatible with the emails that go to each groups. Since we iterate over
    the changes once per group, we want to be sure that for each group
    iteration we're building compatible information.
    """

    name = change.name
    if name in change_by_name:
        if change_by_name[name].verb != change.verb or change_by_name[name].groups != change.groups:
            print "change_by_name=%s" % (change_by_name, )
            print "change: old=%s; new=%s" % (change_by_name[name], change)
            assert False
    else:
        change_by_name[name] = change

def locker_access_diff(the_space, group_data, old_access, new_access, ):
    cac_msgs = [] # [String]
    for mit_id in joint_keys(old_access, new_access):
        change_by_name = {} # name -> LockerAccessChangeEntry
        def safe_add(change):
            safe_add_change_real(change_by_name, change)
        old_by_names = old_access[mit_id]
        new_by_names = new_access[mit_id]
        old_by_group = flip_dict(old_by_names)
        new_by_group = flip_dict(new_by_names)
        unchanged = (old_by_names == new_by_names)
        if unchanged: continue
        print "ID=%s (%s):\n\t%s\t(%s)\n\t%s\t(%s)\n" % (mit_id, unchanged, old_by_names, old_by_group, new_by_names, new_by_group, ),
        for group_pk in joint_keys(old_by_group, new_by_group):
            # TODO: Do we need to do an iteration for each group? This seems
            # slightly questionable. Can we just loop over all known names?

            old_names = old_by_group[group_pk]
            new_names = new_by_group[group_pk]
            for name in old_names.union(new_names):
                changed_groups = old_by_names[name] ^ new_by_names[name]

                def mkchange(verb):
                    change = LockerAccessChangeEntry(
                        mit_id=mit_id,
                        verb=verb,
                        name=name,
                        groups=changed_groups,
                    )
                    if verb == "Keep":
                        change.group_msgs = "(other groups involved)"
                    change.cac_msgs = "(groups: %s -> %s)" % (old_by_names[name], new_by_names[name])
                    return change

                if name in old_names and name in new_names: # keep
                    safe_add(mkchange("Keep"))
                elif name in old_names: # remove from this group
                    if new_by_names[name]: # keep b/c other groups
                        safe_add(mkchange("Keep"))
                    else:
                        safe_add(mkchange("Remove"))
                elif name in new_names: # add for this group
                    if old_by_names[name]: # keep b/c other groups
                        safe_add(mkchange("Keep"))
                    else:
                        safe_add(mkchange("Add"))
                else:
                    assert False, "in old_names or new_names, but not in both, one, or the other..."

        # Handle reporting the results...
        for change in change_by_name.values():
            cac_msgs.append(change.cac_format())
            group_msg = "%s\t%s" % (the_space.number, change.group_format())
            for group_pk in change.groups:
                group_data[group_pk].locker_messages.append(group_msg)
                group_data[group_pk].changes = True

    return cac_msgs

def space_specific_access(the_space, group_data, old_time, new_time, ):
    old_data = the_space.build_access(time=old_time)
    new_data = the_space.build_access(time=new_time)
    all_spaces[the_space.pk] = the_space
    init_groups(group_data, old_data[2])
    init_groups(group_data, new_data[2])
    for group_pk, group_info in group_data.items():
        if group_pk in old_data[0] or group_pk in new_data[0]:
            if the_space.merged_acl:
                group_info.add_locker_signatories(old_data[1], old_time)
                group_info.add_locker_signatories(new_data[1], new_time)
            else:
                group_info.learn_office_access(the_space.pk, old_data[0], new_data[0])
    cac_msgs = []
    if the_space.merged_acl:
        cac_msgs = locker_access_diff(the_space, group_data, old_data[1], new_data[1])
    return cac_msgs

def space_access_diffs():
    new_time = datetime.datetime.utcnow()
    old_time = new_time - datetime.timedelta(days=1, minutes=15)
    bulk_fill_people([old_time, new_time])
    group_data = {} # Group.pk -> GroupInfo
    cac_locker_msgs = []

    process_spaces =  space.models.Space.objects.all()
    for the_space in process_spaces:
        new_cac_msgs = space_specific_access(the_space, group_data, old_time, new_time)
        if new_cac_msgs:
            cac_locker_msgs.append("%s\n%s\n" % (the_space.number, "\n".join(new_cac_msgs)))

    changed_groups = []
    for group_pk, group_info in group_data.items():
        group_info.add_office_signatories(old_time, new_time)
        cac_changes, group_office_changes = group_info.list_office_changes()
        if group_info.changes:
            changed_groups.append((group_info.group, cac_changes, group_office_changes, group_info.locker_messages, ))

    asa_rcpts = ['asa-space@mit.edu', 'asa-db@mit.edu', ]
    if changed_groups:
        util.emails.email_from_template(
            tmpl='space/cac-change-email.txt',
            context={'changed_groups': changed_groups, 'locker_msgs':cac_locker_msgs, },
            subject="Space access updates",
            to=['caclocks@mit.edu'],
            cc=asa_rcpts,
        ).send()
    group_email_cc = asa_rcpts + ['caclocks@mit.edu']
    for group, cac_msg, group_office_msg, group_locker_msgs in changed_groups:
        util.emails.email_from_template(
            tmpl='space/group-change-email.txt',
            context={
                'group':group,
                'office_msg':group_office_msg,
                'locker_msgs':group_locker_msgs,
            },
            subject="[ASA DB] Space access updates for %s" % (group.name, ),
            to=[group.officer_email],
            cc=group_email_cc,
        ).send()


if __name__ == "__main__":
    space_access_diffs()
