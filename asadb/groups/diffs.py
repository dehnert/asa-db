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

from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage, mail_admins
from django.db import connection
from django.db.models import Q
from django.template import Context, Template
from django.template.loader import get_template

import reversion.models

import groups.models
import settings
import util.emails
import util.mailman

update_asa_exec = 'asa-exec@mit.edu'
update_funding_board = 'asa-db@mit.edu'
update_constitution_archive = 'asa-db@mit.edu'

if settings.PRODUCTION_DEPLOYMENT:
    asa_all_groups_list = util.mailman.MailmanList('asa-official')
else:
    asa_all_groups_list = util.mailman.MailmanList('asa-test-mailman')

class DiffCallback(object):
    def start_run(self, since, now, ):
        pass
    def end_run(self, ):
        pass
    def handle_group(self, before, after, before_fields, after_fields, ):
        pass
    def handle_signatories(self, signatories, ):
        pass
    def new_group(self, after, after_fields, ):
        pass

class StaticMailCallback(DiffCallback):
    def __init__(self, fields, address, template, signatories=[]):
        self.fields = fields
        self.address = address
        self.template = template
        self.interesting_signatories = signatories
        self.care_about_groups = True
        self.care_about_signatories = True

    def start_run(self, since, now, ):
        self.updates = []
        self.signatory_updates = []
        self.signatory_type_counts = {
            'Added': {},
            'Expired': {},
        }
        self.since = since
        self.now = now

    def handle_group(self, before, after, before_fields, after_fields, ):
        after_revision = after.revision
        update = "Group: %s (ID #%d)\n" % (after_fields['name'], after_fields['id'], )
        update += "At %s by %s (and possibly other people or times)\n" % (
            after_revision.date_created, after_revision.user, )
        for field in self.fields:
            if before_fields[field] != after_fields[field]:
                update += "%s: '%s' -> '%s'\n" % (
                    field, before_fields[field], after_fields[field], )
        self.updates.append(update)

    def handle_signatories(self, signatories, ):
        prev_group = None
        for signatory in signatories:
            if signatory.end_time > self.now:
                change_type = "Added"
            else:
                change_type = "Expired"
            counter = self.signatory_type_counts[change_type]
            if signatory.role.slug in counter:
                counter[signatory.role.slug] += 1
            else:
                counter[signatory.role.slug] = 0
            if signatory.role.slug in self.interesting_signatories:
                if signatory.group != prev_group:
                    self.signatory_updates.append("")
                self.signatory_updates.append(
                    "%s: %s: %s: %s:\n\trange %s to %s" % (
                        change_type,
                        signatory.group,
                        signatory.role,
                        signatory.person,
                        signatory.start_time.strftime(settings.DATETIME_FORMAT_PYTHON),
                        signatory.end_time.strftime(settings.DATETIME_FORMAT_PYTHON),
                    ))
                prev_group = signatory.group
            else:
                print "Ignoring role %s (signatory %s)" % (signatory.role.slug, signatory, )

    def end_run(self, ):
        message = "\n\n".join(self.updates)
        signatories_message = "\n".join(self.signatory_updates)
        if (self.care_about_groups and self.updates) or (self.care_about_signatories and self.signatory_updates):
            pass
        else:
            return
        tmpl = get_template(self.template)
        ctx = Context({
            'num_groups': len(self.updates),
            'groups_message': message,
            'num_signatory_records': len(self.signatory_updates),
            'signatory_types': self.interesting_signatories,
            'signatory_type_counts': self.signatory_type_counts,
            'signatories_message': signatories_message,
        })
        body = tmpl.render(ctx)
        email = EmailMessage(
            subject='ASA Database Updates',
            body=body,
            from_email='asa-db@mit.edu',
            to=[self.address, ],
            bcc=['asa-db-outgoing@mit.edu', ]
        )
        email.send()
        self.updates = []
        self.signatory_updates = []


class UpdateOfficerListCallback(DiffCallback):
    def start_run(self, since, now, ):
        self.add = []
        self.delete = []

    def end_run(self, ):
        if self.add or self.delete:
            errors = asa_all_groups_list.change_members(self.add, self.delete)
            subject = "asa-official updater"
            if errors:
                subject = "ERROR: " + subject
            context = {
                'listname': asa_all_groups_list.name,
                'add': self.add,
                'delete': self.delete,
                'errors': errors,
            }
            util.emails.email_from_template(
                tmpl='groups/diffs/asa-official-update.txt',
                context=context, subject=subject,
                to=['asa-db@mit.edu'],
            ).send()

    def handle_group(self, before, after, before_fields, after_fields, ):
        if before_fields['officer_email'] != after_fields['officer_email']:
            name = after_fields['name']
            self.add.append((after_fields['name'], after_fields['officer_email'], ))
            self.delete.append(before_fields['officer_email'])

    def new_group(self, after, after_fields, ):
        self.add.append(after_fields['officer_email'])


diff_fields = {
    'name' :            [ update_asa_exec, ],
    'abbreviation' :    [ update_asa_exec, ],
    'officer_email' :   [ update_asa_exec, update_funding_board ],
    'constitution_url': [ update_asa_exec, update_constitution_archive ],
}

def build_callbacks():
    callbacks = []
    callbacks.append(StaticMailCallback(
        fields=['name', 'abbreviation', 'officer_email', 'constitution_url', ],
        address='asa-admin@mit.edu',
        template='groups/diffs/asa-update-mail.txt',
        signatories=['president', 'treasurer', 'financial', ]
    ))
    sao_callback = StaticMailCallback(
        fields=['name', 'abbreviation', 'officer_email', ],
        address='funds@mit.edu',
        template='groups/diffs/sao-update-mail.txt',
        signatories=['president', 'treasurer', 'financial', ]
    )
    sao_callback.care_about_groups = False
    callbacks.append(sao_callback)
    callbacks.append(UpdateOfficerListCallback())
    return callbacks

def recent_groups(since):
    group_type = ContentType.objects.get_by_natural_key(app_label='groups', model='group')
    revisions = reversion.models.Revision.objects.filter(date_created__gte=since)
    versions = reversion.models.Version.objects.filter(revision__in=revisions, content_type=group_type)
    objs = versions.values("content_type", "object_id").distinct()
    return objs

def diff_objects(objs, since, callbacks):
    revs  = reversion.models.Revision.objects.all()
    old_revs = revs.filter(date_created__lte=since)
    new_revs = revs.filter(date_created__gte=since)
    for obj in objs:
        all_versions = reversion.models.Version.objects.filter(content_type=obj['content_type'], object_id=obj['object_id']).order_by('-revision__date_created')
        before_versions = all_versions.filter(revision__in=old_revs)[:1]
        # This object being passed in means that some version changed it.
        after_versions = all_versions.filter(revision__in=new_revs).select_related('revision__user')
        after = after_versions[0]

        if len(before_versions) > 0 or len(after_versions) > 1:
            if len(before_versions) > 0:
                before = before_versions[0]
            else:
                # New group that's been edited since. Diff against the creation
                # (since creation sent mail, but later changes haven't)
                after = after_versions[-1]
            print "Change?: before=%s (%d), after=%s (%d), type=%s, new=%s" % (
                before, before.pk,
                after, after.pk,
                after.type, after.field_dict,
            )
            before_fields = before.field_dict
            after_fields = after.field_dict
            for callback in callbacks:
                callback.handle_group(before, after, before_fields, after_fields)
        else:
            # New group that's only been edited once
            pass

def diff_signatories(since, now, callbacks):
    # First: still around; then added recently
    qobj_added = Q(end_time__gte=now, start_time__gte=since)
    # First: already gone; then it existed for a while; finally expired recently
    qobj_expired = Q(end_time__lte=now, start_time__lte=since, end_time__gte=since)
    changed_signatories = groups.models.OfficeHolder.objects.filter(qobj_added|qobj_expired)
    changed_signatories.order_by('group__name', 'role__display_name', 'person', )
    changed_signatories = changed_signatories.select_related('role', 'group')
    for callback in callbacks: callback.handle_signatories(changed_signatories)

def generate_diffs():
    now = datetime.datetime.now()
    recent = now - datetime.timedelta(hours=24, minutes=15)
    objs = recent_groups(since=recent)
    callbacks = build_callbacks()
    for callback in callbacks: callback.start_run(since=recent, now=now, )
    diff_objects(objs, since=recent, callbacks=callbacks)
    diff_signatories(recent, now, callbacks=callbacks, )
    for callback in callbacks: callback.end_run()

if __name__ == '__main__':
    generate_diffs()
