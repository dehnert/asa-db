#!/usr/bin/python
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import collections
import datetime
import subprocess

import reversion

import groups.models

def gather_constitutions():
    gs = groups.models.Group.active_groups.all()
    additions = []
    changed = []
    for group in gs:
        defaults = dict(
            last_update=datetime.datetime.now(),
            last_download=datetime.datetime.now(),
        )
        constitution, created = groups.models.GroupConstitution.objects.get_or_create(group=group, defaults=defaults)
        if created: print "created record for %s" % (group, )
        constitution.source_url = group.constitution_url
        success, message, old_success = constitution.update()
        if success:
            if message == "new path":
                additions.append(constitution.dest_file)
            if message == 'updated in place' or message == 'new path':
                changed.append(group, )
        if (success != old_success) and (message != "no url"):
            print "%s: success=%s: %s, url=%s" % (group, success, message, constitution.source_url, )
    return additions, changed

def update_repo(additions, changed, ):
    git_dir = groups.models.constitution_dir
    if additions:
        subprocess.check_call(['git', 'add', ] + additions, cwd=git_dir, )
    msg = "Updated constitutions on %s\n\n%d added, %d changed total.\n\n %4s\tGroup\n%s" % (
        datetime.datetime.now(),
        len(additions),
        len(changed),
        "ID#",
        "\n".join(["%4d:\t%s" % (group.pk, group.name, ) for group in changed]),
    )
    subprocess.check_call(['git', 'commit', '--allow-empty', '-a', '-m', msg, ], cwd=git_dir, )

def webstat():
    constitutions = groups.models.GroupConstitution.objects.all()
    codes = collections.defaultdict(list)
    count = 0
    for const in constitutions:
        if count % 10 == 0: print count,
        code = const.webstat()
        codes[code].append(const)
        count += 1
    for code, gs in codes.items():
        print "\nCode: %s (count: %d)" % (code, len(gs), )
        for const in gs:
            print const.group
    for code, gs in codes.items():
        print "\nCode: %s (count: %d)" % (code, len(gs), )
        for const in gs:
            print const.source_url
    print "\n\n"
    for code, gs in codes.items():
        print "%4d\t%s" % (len(gs), code, )

def list_constitutions():
    constitutions = groups.models.GroupConstitution.objects.all()
    for const in constitutions:
        if const.dest_file: print const.dest_file

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == "gather":
        with reversion.create_revision():
            additions, changed = gather_constitutions()
            importer = django.contrib.auth.models.User.objects.get(username='gather-constitutions@SYSTEM', )
            reversion.set_user(importer)
            reversion.set_comment("gather constitutions")

        update_repo(additions, changed)
    elif sys.argv[1] == "webstat":
        webstat()
    elif sys.argv[1] == "list":
        list_constitutions()
    else:
        raise NotImplementedError
