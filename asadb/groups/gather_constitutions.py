#!/usr/bin/python
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import datetime
import subprocess

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

if __name__ == '__main__':
    additions, changed = gather_constitutions()
    update_repo(additions, changed)
