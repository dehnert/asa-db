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

from django.db import transaction
import django.contrib.auth.models
import reversion

import groups.models
import util.emails

def select_groups(select, src):
    raw_vals = [val.strip() for val in src]
    if select == 'id':
        vals = [int(val) for val in raw_vals]
    elif select == 'name':
        vals = raw_vals
    else:
        raise NotImplementedError, "Selecting by %s not supported" % (select, )
    gs = groups.models.Group.objects
    if select == 'id':
        gs = gs.filter(id__in=vals)
    else:
        gs = gs.filter(name__in=vals)
    return gs

def setup_revision(user, status):
    if user is not None:
        updater = django.contrib.auth.models.User.objects.get(username=user)
    else:
        updater = None
    reversion.set_user(updater)
    reversion.set_comment("Set status to %s" % (status.name, ))

def output_group(out, g, new_status, email):
    pres_emails = ["%s@mit.edu" % (holder.person, ) for holder in g.officers('president')]
    treas_emails = ["%s@mit.edu" % (holder.person, ) for holder in g.officers('treasurer')]
    all_emails = [g.officer_email] + pres_emails + treas_emails
    out.writerow({
        'id':   g.pk,
        'name': g.name,
        'old_status':   g.group_status,
        'email':    ', '.join(all_emails),
        'officer_email': g.officer_email,
        'pres_emails':  ', '.join(pres_emails),
        'treas_emails': ', '.join(treas_emails),
    })
    email_obj = None
    if email:
        ctx = {
            'group': g,
            'new_status': new_status,
        }
        email_obj = util.emails.email_from_template(email, ctx,
            subject="[ASA] %s has been derecognized" % (g.name, ),
            from_email='asa-exec@mit.edu',
            to=[g.officer_email], cc=pres_emails+treas_emails,
        )
        email_obj.bcc.append('asa-admin@mit.edu')
        email_obj.extra_headers['Reply-To'] = 'asa-exec@mit.edu'
    return email_obj

def update_group(g, status, message, user):
    g.group_status = status
    g.set_updater(user)
    g.save()
    if message:
        note = groups.models.GroupNote(
            author=user,
            body=message,
            acl_read_group=True,
            acl_read_offices=True,
            group=g,
        )
        note.save()


@transaction.commit_on_success
def process_changes(status, select, message, user, email):
    # TODO: list groups that couldn't be found
    # TODO: dump group name, emails (officer+pres+treas?), maybe old status?
    fieldnames=['id', 'name', 'old_status', 'email', 'officer_email', 'pres_emails', 'treas_emails', ]
    out = csv.DictWriter(
        sys.stdout,
        fieldnames=fieldnames,
    )
    out.writerow(dict(zip(fieldnames, fieldnames)))
    gs = select_groups(select, sys.stdin)
    status_obj = groups.models.GroupStatus.objects.get(slug=status)
    with reversion.create_revision():
        setup_revision(user, status_obj)
        for g in gs:
            email_obj = output_group(out, g, status_obj, email)
            update_group(g, status_obj, message, user)
            if email_obj: email_obj.send()

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--select-by", dest="select",
                      help="take a list of TYPE on stdin (name or id)", metavar="TYPE")
    parser.add_option("-m", "--message", dest="message",
                      help="add a note saying MESSAGE", metavar="MESSAGE")
    parser.add_option("--user", dest="user",
                      help="username of person executing script")
    parser.add_option("--email", dest="email",
                      help="send an email using TEMPLATE to the groups' officers", metavar="TEMPLATE")
    parser.set_defaults(
        select='id',
        message=None,
        author=None,
        email=None,
    )
    (options, args) = parser.parse_args()
    assert len(args) == 1
    status = args[0]
    process_changes(status, select=options.select, message=options.message, user=options.user, email=options.email, )
