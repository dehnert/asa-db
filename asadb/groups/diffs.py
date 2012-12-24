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
import util.mailinglist

if settings.PRODUCTION_DEPLOYMENT:
    asa_all_groups_list = util.mailinglist.MailmanList('asa-official')
    gsc_fb_list = util.mailinglist.MailmanList('gsc-fb-')
    finboard_groups_list = util.mailinglist.MoiraList('finboard-groups-only')
else:
    asa_all_groups_list = util.mailinglist.MailmanList('asa-test-mailman')
    gsc_fb_list = util.mailinglist.MailmanList('asa-test-mailman')
    finboard_groups_list = util.mailinglist.MoiraList('asa-test-moira')

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
            'Added': collections.defaultdict(lambda: 0),
            'Expired': collections.defaultdict(lambda: 0),
        }
        self.signatory_types_seen = set()
        self.since = since
        self.now = now

    def handle_group(self, before, after, before_fields, after_fields, ):
        after_revision = after.revision
        update = "Group: %s (ID #%d)\n" % (after_fields['name'], after_fields['id'], )
        update += "  At %s by %s (and possibly other people or times)\n" % (
            after_revision.date_created, after_revision.user, )
        for field in self.fields:
            if before_fields[field] != after_fields[field]:
                update += '  %18s: %12s -> %12s\n' % (
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
            counter[signatory.role.slug] += 1
            self.signatory_types_seen.add(signatory.role.slug)
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
                pass
                #print "Ignoring role %s (signatory %s)" % (signatory.role.slug, signatory, )

    def build_change_stats(self, ):
        lines = []
        care_about = 0

        line = "%20s" % ("", )
        change_types = self.signatory_type_counts.keys()
        for change_type in change_types:
            line += "\t%s" % (change_type, )
        lines.append(line); line = ""

        for sig_type in self.signatory_types_seen:
            anno_sig = sig_type
            if sig_type in self.interesting_signatories:
                anno_sig += " "
            else:
                anno_sig += "*"
            line += "%20s" % (anno_sig, )
            for change_type in change_types:
                if sig_type in self.signatory_type_counts[change_type]:
                    count = self.signatory_type_counts[change_type][sig_type]
                else:
                    count = 0
                if sig_type in self.interesting_signatories:
                    care_about += count
                out = "\t%4d" % (count, )
                line += out
            lines.append(line); line = ""

        line = "* Details for this signatory type not included in email."
        lines.append(line)

        return "\n".join(lines), care_about

    def end_run(self, ):
        change_stats, care_about = self.build_change_stats()
        print "\nChange stats for email to %s:" % (self.address, )
        print change_stats

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
            'care_about': care_about,
            'change_stats': change_stats,
            'signatory_types': self.interesting_signatories,
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
    def __init__(self, listobj, include_pred=None):
        self.listobj = listobj
        if not include_pred:
            include_pred = lambda version, fields: True
        self.include_pred = include_pred

    def start_run(self, since, now, ):
        self.add = []
        self.delete = []
        self.notes = []

    def end_run(self, ):
        if self.add or self.delete:
            errors = self.listobj.change_members(self.add, self.delete)
            listname = self.listobj.name
            subject = "[ASA DB] %s updater" % (listname, )
            if errors:
                subject = "ERROR: " + subject
            context = {
                'listname': listname,
                'add': self.add,
                'delete': self.delete,
                'errors': errors,
                'notes': self.notes,
            }
            util.emails.email_from_template(
                tmpl='groups/diffs/list-update.txt',
                context=context, subject=subject,
                to=['asa-db@mit.edu'],
            ).send()

    def update_changes(self, change_list, phase_name, name, addr, include, force_note=False, ):
        """
        Given an address and whether to process this item, update a list as appropriate and supply appropriate diagnostic notes.
        """

        note = None
        if addr and include:
            change_list.append((name, addr, ))
            if force_note:
                note = "email address is %s" % (addr, )
        elif not include:
            note = "doesn't pass predicate"
        elif not addr:
            note = "address is blank"
        else:
            note = "Something weird happened while adding (addr='%s', include=%s)" % (addr, include)
        if note:
            self.notes.append("%8s: %s: %s" % (phase_name, name, note, ))

    def handle_group(self, before, after, before_fields, after_fields, ):
        before_include = self.include_pred(before, before_fields)
        after_include = self.include_pred(after, after_fields)
        before_addr = before_fields['officer_email']
        after_addr  = after_fields['officer_email']

        # check if a change is appropriate
        effective_before_addr = before_addr if before_include else None
        effective_after_addr = after_addr if after_include else None

        if effective_before_addr != effective_after_addr:
            name = after_fields['name']
            self.update_changes(self.delete, "Delete", name, before_addr, before_include)
            self.update_changes(self.add, "Add", name, after_addr, after_include)

    def new_group(self, after, after_fields, ):
        name = after_fields['name']
        email = after_fields['officer_email']
        include = self.include_pred(after, after_fields)
        self.update_changes(self.add, "New", name, email, include, force_note=True)


def default_active_pred():
    status_objs = groups.models.GroupStatus.objects.filter(slug__in=['active', 'suspended', 'nge'])
    status_pks = [status.pk for status in status_objs]
    def pred(version, fields):
        return fields['group_status'] in status_pks
    return pred

def funded_pred(funding_slug):
    classes = groups.models.GroupClass.objects
    class_pk = classes.get(slug='mit-funded').pk
    fundings = groups.models.GroupFunding.objects
    fund_pk = fundings.get(slug=funding_slug).pk
    active_pred = default_active_pred()
    def pred(version, fields):
        return active_pred(version, fields) and fields['group_class'] == class_pk and fields['group_funding'] == fund_pk
    return pred


# Note: these aren't actually used (but might have some utility in telling what
# should be diffed)
update_asa_exec = 'asa-exec@mit.edu'
update_funding_board = 'asa-db@mit.edu'
update_constitution_archive = 'asa-db@mit.edu'

diff_fields = {
    'name' :            [ update_asa_exec, ],
    'abbreviation' :    [ update_asa_exec, ],
    'officer_email' :   [ update_asa_exec, update_funding_board ],
    'constitution_url': [ update_asa_exec, update_constitution_archive ],
}

# This is used, OTOH
def build_callbacks():
    callbacks = []
    callbacks.append(StaticMailCallback(
        fields=[
            'name', 'abbreviation',
            'officer_email', 'group_email', 'athena_locker',
            'website_url', 'constitution_url',
            'activity_category', 'group_class', 'group_status', 'group_funding',
            'advisor_name',
            'num_undergrads', 'num_grads', 'num_community', 'num_other',
            'main_account_id', 'funding_account_id',
        ],
        address='asa-internal@mit.edu',     # some of these fields aren't public
        template='groups/diffs/asa-update-mail.txt',
        signatories=['president', 'treasurer', 'financial', 'group-admin', 'temp-admin', ]
    ))
    sao_callback = StaticMailCallback(
        fields=['name', 'abbreviation', 'officer_email', ],
        address='funds@mit.edu',
        template='groups/diffs/sao-update-mail.txt',
        signatories=['president', 'treasurer', 'financial', ]
    )
    sao_callback.care_about_groups = False
    callbacks.append(sao_callback)
    callbacks.append(UpdateOfficerListCallback(
        listobj=asa_all_groups_list,
        include_pred=default_active_pred(),
    ))
    callbacks.append(UpdateOfficerListCallback(
        listobj=finboard_groups_list,
        include_pred=funded_pred('undergrad'),
    ))
    callbacks.append(UpdateOfficerListCallback(
        listobj=gsc_fb_list,
        include_pred=funded_pred('grad'),
    ))
    return callbacks

def recent_groups(since):
    group_type = ContentType.objects.get_by_natural_key(app_label='groups', model='group')
    revisions = reversion.models.Revision.objects.filter(date_created__gte=since)
    versions = reversion.models.Version.objects.filter(revision__in=revisions, content_type=group_type)
    objs = versions.values("content_type", "object_id").distinct()
    return objs

def diff_objects(objs, since, callbacks, stats, ):
    revs  = reversion.models.Revision.objects.all()
    old_revs = revs.filter(date_created__lte=since)
    new_revs = revs.filter(date_created__gte=since)
    for obj in objs:
        all_versions = reversion.models.Version.objects.filter(content_type=obj['content_type'], object_id=obj['object_id']).order_by('-revision__date_created')
        before_versions = all_versions.filter(revision__in=old_revs)[:1]
        # This object being passed in means that some version changed it.
        after_versions = all_versions.filter(revision__in=new_revs).select_related('revision__user')
        after = after_versions[0]
        after_fields = after.field_dict

        if len(before_versions) > 0 or len(after_versions) > 1:
            if len(before_versions) > 0:
                before = before_versions[0]
                stats['change_old'] += 1
            else:
                # New group that's been edited since. Diff against the creation
                # (since creation sent mail, but later changes haven't)
                before = after_versions.reverse()[0]
                stats['change_new'] += 1
            stats['change_total'] += 1
            #print "Change?: before=%s (%d), after=%s (%d), type=%s, new=%s" % (
            #    before, before.pk,
            #    after, after.pk,
            #    after.type, after.field_dict,
            #)
            before_fields = before.field_dict
            for callback in callbacks:
                callback.handle_group(before, after, before_fields, after_fields)
        else:
            # New group that's only been edited once
            # Note that "normal" new groups will have their startup form
            # (which creates the Group object) and the approval (which makes
            # more changes, so this is group startups + NGEs, not actually
            # normal new groups)
            stats['new_group'] += 1
            callback.new_group(after, after_fields)

def diff_signatories(since, now, callbacks):
    # First: still around; then added recently
    qobj_added = Q(end_time__gte=now, start_time__gte=since)
    # First: already gone; then it existed for a while; finally expired recently
    qobj_expired = Q(end_time__lte=now, start_time__lte=since, end_time__gte=since)
    changed_signatories = groups.models.OfficeHolder.objects.filter(qobj_added|qobj_expired)
    changed_signatories = changed_signatories.order_by('group__name', 'role__display_name', 'person', )
    changed_signatories = changed_signatories.select_related('role', 'group')
    for callback in callbacks: callback.handle_signatories(changed_signatories)

def generate_diffs():
    now = datetime.datetime.now()
    recent = now - datetime.timedelta(hours=24, minutes=15)
    objs = recent_groups(since=recent)
    callbacks = build_callbacks()
    stats = collections.defaultdict(lambda: 0)
    for callback in callbacks: callback.start_run(since=recent, now=now, )
    diff_objects(objs, since=recent, callbacks=callbacks, stats=stats)
    diff_signatories(recent, now, callbacks=callbacks, )
    for callback in callbacks: callback.end_run()

    print "\nOverall change stats:"
    for stat_key, stat_val in stats.items():
        print "%20s:\t%6d" % (stat_key, stat_val, )
    print ""

if __name__ == '__main__':
    generate_diffs()
