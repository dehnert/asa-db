# Create your views here.

import collections
import datetime

import groups.models

from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage, mail_admins
from django import forms
from django.forms import ValidationError
from django.db import connection
from django.db.models import Q

import form_utils.forms
import reversion.models
import django_filters

from util.db_form_utils import StaticWidget
from util.emails import email_from_template



############
# Homepage #
############

def view_homepage(request, ):
    users_groups = []
    groupmsg = ""
    has_perms = []
    if request.user.is_authenticated():
        username = request.user.username
        current_officers = groups.models.OfficeHolder.current_holders.filter(person=username)
        users_groups = groups.models.Group.objects.filter(officeholder__in=current_officers).distinct()

        perms = []
        perms.extend(groups.models.Group._meta.permissions)
        perms.extend(groups.models.GroupNote._meta.permissions)
        perms += (
            ('change_group', 'Change arbitrary group information', ),
        )
        for perm_name, perm_desc in perms:
            if request.user.has_perm('groups.%s' % (perm_name, )):
                has_perms.append((perm_name, perm_desc, ))

    context = {
        'groups': users_groups,
        'groupmsg': groupmsg,
        'has_perms': has_perms,
        'pagename': 'homepage',
    }
    return render_to_response('index.html', context, context_instance=RequestContext(request), )



################
# Single group #
################

class GroupDetailView(DetailView):
    context_object_name = "group"
    model = groups.models.Group
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        group = context['group']

        # Indicate whether this person should be able to see "private" info
        context['viewpriv'] = self.request.user.has_perm('groups.view_group_private_info', group)
        context['adminpriv'] = self.request.user.has_perm('groups.admin_group', group)
        context['notes'] = group.viewable_notes(self.request.user)

        # People involved in the group
        just_roles = groups.models.OfficerRole.objects.all()
        if context['viewpriv'] or self.request.user.has_perm('groups.view_signatories'):
            # Can see the non-public stuff
            pass
        else:
            just_roles = just_roles.filter(publicly_visible=True)
        roles = []
        for role in just_roles:
            roles.append((role.display_name, role, group.officers(role=role), ))
        context['roles'] = roles

        return context


class GroupChangeMainForm(form_utils.forms.BetterModelForm):
    def __init__(self, *args, **kwargs):
        change_restricted = False
        if 'change_restricted' in kwargs:
            change_restricted = kwargs['change_restricted']
            del kwargs['change_restricted']
        super(GroupChangeMainForm, self).__init__(*args, **kwargs)
        restricted_fields = list(self.nobody_fields)
        if change_restricted:
            restricted_fields.extend(self.exec_only_fields)
        for field_name in restricted_fields:
            formfield = self.fields[field_name]
            value = getattr(self.instance, field_name)
            StaticWidget.replace_widget(formfield, value)

    exec_only_fields = [
        'name', 'abbreviation',
        'group_status', 'group_class',
        'group_funding', 'main_account_id', 'funding_account_id',
    ]
    nobody_fields = [
        'recognition_date',
    ]

    class Meta:
        fieldsets = [
            ('basic', {
                'legend': 'Basic Information',
                'fields': ['name', 'abbreviation', 'activity_category', 'description', ],
            }),
            ('size', {
                'legend':'Membership Numbers',
                'fields': ['num_undergrads', 'num_grads', 'num_community', 'num_other',],
            }),
            ('contact', {
                'legend': 'Contact Information',
                'fields': ['website_url', 'meeting_times', 'officer_email', 'group_email', ],
            }),
            ('recognition', {
                'legend': 'Recognition',
                'fields': ['group_status', 'group_class', 'recognition_date', ],
            }),
            ('financial', {
                'legend': 'Financial Information',
                'fields': ['group_funding', 'main_account_id', 'funding_account_id', ],
            }),
            ('more-info', {
                'legend': 'Additional Information',
                'fields': ['constitution_url', 'advisor_name', 'athena_locker', ],
            }),
        ]
        model = groups.models.Group

def manage_main(request, pk, ):
    group = get_object_or_404(groups.models.Group, pk=pk)

    if not request.user.has_perm('groups.admin_group', group):
        raise PermissionDenied
    change_restricted = True
    if request.user.has_perm('groups.change_group', group):
        change_restricted = False

    msg = None

    initial = {}
    if request.method == 'POST': # If the form has been submitted...
        # A form bound to the POST data
        form = GroupChangeMainForm(
            request.POST, request.FILES,
            change_restricted=change_restricted,
            instance=group,
        )

        if form.is_valid(): # All validation rules pass
            request_obj = form.save(commit=False)
            request_obj.set_updater(request.user)
            request_obj.save()
            form.save_m2m()
            msg = "Thanks for editing!"
        else:
            msg = "Validation failed. See below for details."

    else:
        form = GroupChangeMainForm(change_restricted=change_restricted, instance=group, initial=initial, ) # An unbound form

    context = {
        'group': group,
        'form':  form,
        'msg':   msg,
    }
    return render_to_response('groups/group_change_main.html', context, context_instance=RequestContext(request), )


##################
# GROUP CREATION #
##################

def validate_athena(username, student=False, ):
    try:
        person = groups.models.AthenaMoiraAccount.active_accounts.get(username=username)
        if student and not person.is_student():
            raise ValidationError('This must be a current student.')
    except groups.models.AthenaMoiraAccount.DoesNotExist:
        raise ValidationError('This must be a valid Athena username.')


class GroupCreateForm(form_utils.forms.BetterModelForm):
    create_officer_list = forms.BooleanField(required=False)
    create_group_list = forms.BooleanField(required=False)
    create_athena_locker = forms.BooleanField(required=False)

    president_name = forms.CharField(max_length=50, )
    president_kerberos = forms.CharField(min_length=3, max_length=8, )
    treasurer_name = forms.CharField(max_length=50)
    treasurer_kerberos = forms.CharField(min_length=3, max_length=8, )
    def clean_president(self, ):
        username = self.cleaned_data['president_kerberos']
        validate_athena(username, True, )
        return username

    def clean_treasurer(self, ):
        username = self.cleaned_data['treasurer_kerberos']
        validate_athena(username, True, )
        return username

    class Meta:
        fieldsets = [
            ('basic', {
                'legend': 'Basic Information',
                'fields': ['name', 'abbreviation', 'description', ],
            }),
            ('officers', {
                'legend': 'Officers',
                'fields': ['president_name', 'president_kerberos', 'treasurer_name', 'treasurer_kerberos', ],
            }),
            ('type', {
                'legend': 'Type',
                'fields': ['activity_category', 'group_class', 'group_funding', ],
            }),
            ('technical', {
                'legend': 'Technical Information',
                'fields': [
                    'officer_email', 'create_officer_list',
                    'group_email', 'create_group_list',
                    'athena_locker', 'create_athena_locker',
                ],
            }),
            ('financial', {
                'legend': 'Financial Information',
                'fields': ['main_account_id', 'funding_account_id', ],
            }),
            ('constitution', {
                'legend': 'Constitution',
                'fields': ['constitution_url', ],
            }),
        ]
        model = groups.models.Group


class GroupCreateNgeForm(GroupCreateForm):
    def __init__(self, *args, **kwargs):
        super(GroupCreateNgeForm, self).__init__(*args, **kwargs)
        self.fields['treasurer_name'].required = False
        self.fields['treasurer_kerberos'].required = False


class GroupCreateStartupForm(GroupCreateForm):
    def __init__(self, *args, **kwargs):
        super(GroupCreateStartupForm, self).__init__(*args, **kwargs)
        self.fields['activity_category'].required = True
        self.fields['constitution_url'].required = True
        self.fields['constitution_url'].help_text = "Please put a copy of your finalized constitution on a publicly-accessible website (e.g. your group's, or your own, Public folder), and link to it in the box above."

    class Meta(GroupCreateForm.Meta):
        fieldsets = filter(
            lambda fieldset: fieldset[0] not in ['financial', ],
            GroupCreateForm.Meta.fieldsets
        )

def create_group_get_emails(group, group_startup, officer_emails, ):
    # Figure out all the accounts mail parameters
    accounts_count = 0
    create_officer_list = False
    if group_startup.create_officer_list and group.officer_email:
        create_officer_list = True
        accounts_count += 1
    create_group_list = False
    if group_startup.create_group_list and group.group_email:
        create_group_list = True
        accounts_count += 1
    create_athena_locker = False
    if group_startup.create_athena_locker and group.athena_locker:
        create_athena_locker = True
        accounts_count += 1
    officer_list, _, officer_domain = group.officer_email.partition('@')
    group_list, _, group_domain = group.group_email.partition('@')

    # Fill out the Context
    mail_context = Context({
        'group': group,
        'group_startup': group_startup,
        'create_officer_list': create_officer_list,
        'create_group_list': create_group_list,
        'create_athena_locker': create_athena_locker,
        'officer_list': officer_list,
        'group_list': group_list,
        'officer_emails': officer_emails,
    })

    # Welcome mail
    welcome_mail = email_from_template(
        tmpl='groups/diffs/new-group-announce.txt',
        context=mail_context,
        subject='ASA Group Recognition: %s' % (group.name, ),
        to=officer_emails,
        cc=['asa-new-group-announce@mit.edu'],
        from_email='asa-exec@mit.edu',
    )

    # Accounts mail
    if accounts_count > 0:
        accounts_mail = email_from_template(
            tmpl='groups/diffs/new-group-accounts.txt',
            context=mail_context,
            subject='New Student Activity: %s' % (group.name, ),
            to=['accounts@mit.edu'],
            cc=officer_emails+['asa-admin@mit.edu'],
            from_email='asa-admin@mit.edu',
        )
        # XXX: Handle this better
        if officer_domain != 'mit.edu' or (create_group_list and group_domain != 'mit.edu'):
            accounts_mail.to = ['asa-groups@mit.edu']
            accounts_mail.cc = ['asa-db@mit.edu']
            accounts_mail.subject = "ERROR: " + accounts_mail.subject
            accounts_mail.body = "Bad domain on officer or group list\n\n" + accounts_mail.body

    else:
        accounts_mail = None
    return welcome_mail, accounts_mail

def create_group_officers(group, formdata, save=True, ):
    officer_emails = [ ]
    for officer in ('president', 'treasurer', ):
        username = formdata[officer+'_kerberos']
        if username:
            if save: groups.models.OfficeHolder(
                person=username,
                role=groups.models.OfficerRole.objects.get(slug=officer),
                group=group,
            ).save()
            officer_emails.append('%s@mit.edu' % (formdata[officer+'_kerberos'], ))
    return officer_emails

@permission_required('groups.recognize_nge')
def recognize_nge(request, ):
    msg = None

    initial = {
        'create_officer_list': False,
        'create_group_list': False,
        'create_athena_locker': True,
    }
    group = groups.models.Group()
    group.group_status = groups.models.GroupStatus.objects.get(slug='nge', )
    group.recognition_date  = datetime.datetime.now()
    if request.method == 'POST': # If the form has been submitted...
        # A form bound to the POST data
        form = GroupCreateNgeForm(
            request.POST, request.FILES,
            initial=initial,
            instance=group,
        )

        if form.is_valid(): # All validation rules pass
            group.set_updater(request.user)
            form.save()
            officer_emails = create_group_officers(group, form.cleaned_data, )

            return redirect(reverse('groups:group-detail', args=[group.pk]))
        else:
            msg = "Validation failed. See below for details."

    else:
        form = GroupCreateNgeForm(initial=initial, instance=group, ) # An unbound form

    context = {
        'form':  form,
        'msg':   msg,
        'pagename':   'groups',
    }
    return render_to_response('groups/create/nge.html', context, context_instance=RequestContext(request), )

def startup_form(request, ):
    msg = None

    initial = {
        'create_officer_list': True,
        'create_group_list': True,
        'create_athena_locker': True,
    }
    group = groups.models.Group()
    group.group_status = groups.models.GroupStatus.objects.get(slug='applying', )
    group.recognition_date  = datetime.datetime.now()
    if request.method == 'POST': # If the form has been submitted...
        # A form bound to the POST data
        form = GroupCreateStartupForm(
            request.POST, request.FILES,
            initial=initial,
            instance=group,
        )

        if form.is_valid(): # All validation rules pass
            group.set_updater(request.user)
            form.save()

            group_startup = groups.models.GroupStartup()
            group_startup.group = group
            group_startup.stage = groups.models.GROUP_STARTUP_STAGE_SUBMITTED
            group_startup.submitter = request.user.username

            group_startup.create_officer_list = form.cleaned_data['create_officer_list']
            group_startup.create_group_list = form.cleaned_data['create_group_list']
            group_startup.create_athena_locker = form.cleaned_data['create_athena_locker']

            group_startup.president_name = form.cleaned_data['president_name']
            group_startup.president_kerberos = form.cleaned_data['president_kerberos']
            group_startup.treasurer_name = form.cleaned_data['treasurer_name']
            group_startup.treasurer_kerberos = form.cleaned_data['treasurer_kerberos']

            group_startup.save()

            context = {
                'group':            group,
                'group_startup':    group_startup,
                'pagename':         'groups',
            }

            email_from_template(
                tmpl='groups/create/startup-submitted-email.txt',
                context=context,
                subject='ASA Startup Application: %s' % (group.name, ),
                to=[request.user.email] + create_group_officers(group, form.cleaned_data, save=False, ),
                cc=['asa-groups@mit.edu'],
                from_email='asa-groups@mit.edu',
            ).send()

            return render_to_response('groups/create/startup_thanks.html', context, context_instance=RequestContext(request), )
        else:
            msg = "Validation failed. See below for details."

    else:
        form = GroupCreateStartupForm(initial=initial, instance=group, ) # An unbound form

    context = {
        'form':  form,
        'msg':   msg,
        'pagename':   'groups',
    }
    return render_to_response('groups/create/startup.html', context, context_instance=RequestContext(request), )

class GroupRecognitionForm(forms.Form):
    test = forms.BooleanField()

@permission_required('groups.recognize_group')
def recognize_normal_group(request, pk, ):
    group_startup = get_object_or_404(groups.models.GroupStartup, pk=pk, )
    group = group_startup.group

    context = {
        'startup': group_startup,
        'group': group,
        'pagename' : 'groups',
    }

    if group.group_status.slug != 'applying':
        return render_to_response('groups/create/err.not-applying.html', context, context_instance=RequestContext(request), )
    if group_startup.stage != groups.models.GROUP_STARTUP_STAGE_SUBMITTED:
        return render_to_response('groups/create/err.not-applying.html', context, context_instance=RequestContext(request), )

    context['msg'] = ""
    if request.method == 'POST':
        if 'approve' in request.POST:
            group_startup.stage = groups.models.GROUP_STARTUP_STAGE_APPROVED
            group_startup.save()

            group.group_status = groups.models.GroupStatus.objects.get(slug='active')
            group.constitution_url = ""
            group.recognition_date = datetime.datetime.now()
            group.set_updater(request.user)

            group.save()
            officer_emails = create_group_officers(group, group_startup.__dict__, )
            welcome_mail, accounts_mail = create_group_get_emails(group, group_startup, officer_emails, )
            welcome_mail.send()
            if accounts_mail:
                accounts_mail.send()
            context['msg'] = 'Group approved.'
            context['msg_type'] = 'info'
        elif 'reject' in request.POST:
            group_startup.stage = groups.models.GROUP_STARTUP_STAGE_REJECTED
            group_startup.save()
            group.group_status = groups.models.GroupStatus.objects.get(slug='derecognized')
            group.save()
            note = groups.models.GroupNote(
                author=request.user.username,
                body="Group rejected during recognition process.",
                acl_read_group=True,
                acl_read_offices=True,
                group=group,
            ).save()
            context['msg'] = 'Group rejected.'
            context['msg_type'] = 'info'
        else:
            context['disp_form'] = True
    else:
        context['disp_form'] = True

    return render_to_response('groups/create/startup_review.html', context, context_instance=RequestContext(request), )

class GroupStartupListView(ListView):
    model = groups.models.GroupStartup
    template_object_name = 'startup'

    def get_queryset(self, ):
        qs = super(GroupStartupListView, self).get_queryset()
        qs = qs.filter(stage=groups.models.GROUP_STARTUP_STAGE_SUBMITTED)
        qs = qs.select_related('group')
        return qs

    def get_context_data(self, **kwargs):
        context = super(GroupStartupListView, self).get_context_data(**kwargs)
        context['pagename'] = 'groups'
        return context


##################
# Multiple group #
##################

class GroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains', label="Name contains")
    abbreviation = django_filters.CharFilter(lookup_type='iexact', label="Abbreviation is")

    class Meta:
        model = groups.models.Group
        fields = [
            'name',
            'abbreviation',
            'activity_category',
            'group_class',
            'group_status',
            'group_funding',
        ]


class GroupListView(ListView):
    model = groups.models.Group
    template_object_name = 'group'

    def get(self, *args, **kwargs):
        qs = super(GroupListView, self).get_queryset()
        self.filterset = GroupFilter(self.request.GET, qs)
        return super(GroupListView, self).get(*args, **kwargs)

    def get_queryset(self, ):
        qs = self.filterset.qs
        return qs

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)
        # Add in the publisher
        context['pagename'] = 'groups'
        context['filter'] = self.filterset
        return context


def load_officers(group, ):
    officers = group.officers()
    people = list(set([ officer.person for officer in officers ]))
    roles  = groups.models.OfficerRole.objects.all()

    officers_map = {}
    for officer in officers:
        officers_map[(officer.person, officer.role)] = officer

    return people, roles, officers_map

def manage_officers(request, pk, ):
    group = get_object_or_404(groups.models.Group, pk=pk)

    if not request.user.has_perm('groups.admin_group', group):
        raise PermissionDenied

    max_new = 4

    people, roles, officers_map = load_officers(group)

    msgs = []
    changes = []
    edited = False
    kept = 0
    kept_not = 0
    if request.method == 'POST': # If the form has been submitted
        edited = True

        new_people = {}
        moira_accounts = {}
        for i in range(max_new):
            key = "extra.%d" % (i, )
            if key in request.POST and request.POST[key] != "":
                username = request.POST[key]
                try:
                    moira_accounts[username] = groups.models.AthenaMoiraAccount.active_accounts.get(username=username)
                    new_people[i] = username
                except groups.models.AthenaMoiraAccount.DoesNotExist:
                    msgs.append('Athena account "%s" appears not to exist. Changes involving them have been ignored.' % (username, ))
        for person in people:
            try:
                moira_accounts[person] = groups.models.AthenaMoiraAccount.active_accounts.get(username=person)
            except groups.models.AthenaMoiraAccount.DoesNotExist:
                msgs.append('Athena account "%s" appears not to exist. They can not be added to new roles. You should remove them from any roles they hold, if you have not already.' % (person, ))
        for role in roles:
            key = "holders.%s" % (role.slug, )
            new_holders = set()
            if key in request.POST:
                new_holders = set(request.POST.getlist(key, ))
            if len(new_holders) > role.max_count:
                msgs.append("You selected %d people for %s; only %d are allowed. No changes to %s have been carried out in this update." %
                    (len(new_holders), role.display_name, role.max_count, role.display_name, )
                )
            else:
                for person in people:
                    if person in new_holders:
                        if (person, role) in officers_map:
                            if role.require_student and not moira_accounts[person].is_student():
                                msgs.append('Only students can have the %s role, and %s does not appear to be a student. (If this is not the case, please contact us.) You should replace this person ASAP.' % (role, person, ))
                            #changes.append(("Kept", "yellow", person, role))
                            kept += 1
                        else:
                            if person not in moira_accounts:
                                msgs.append('Could not add nonexistent Athena account "%s" as %s.' % (person, role, ))
                            elif role.require_student and not moira_accounts[person].is_student():
                                msgs.append('Only students can have the %s role, and %s does not appear to be a student. (If this is not the case, please contact us.)' % (role, person, ))
                            else:
                                holder = groups.models.OfficeHolder(person=person, role=role, group=group,)
                                holder.save()
                                changes.append(("Added", "green", person, role))
                    else:
                        if (person, role) in officers_map:
                            officers_map[(person, role)].expire()
                            changes.append(("Removed", "red", person, role))
                        else:
                            kept_not += 1
                            pass
                for i in range(max_new):
                    if "extra.%d" % (i, ) in new_holders:
                        if i in new_people:
                            person = new_people[i]
                            if role.require_student and not moira_accounts[person].is_student():
                                msgs.append('Only students can have the %s role, and %s does not appear to be a student.' % (role, person, ))
                            else:
                                holder = groups.models.OfficeHolder(person=person, role=role, group=group,)
                                holder.save()
                                changes.append(("Added", "green", person, role))

        # mark as changed and reload the data
        if changes:
            group.set_updater(request.user)
            group.save()
        people, roles, officers_map = load_officers(group)

    officers_data = []
    for person in people:
        role_list = []
        for role in roles:
            if (person, role) in officers_map:
                role_list.append((role, True))
            else:
                role_list.append((role, False))
        officers_data.append((False, person, role_list))
    null_role_list = [(role, False) for role in roles]
    for i in range(max_new):
        officers_data.append((True, "extra.%d" % (i, ), null_role_list))

    context = {
        'group': group,
        'roles': roles,
        'people': people,
        'officers': officers_data,
        'edited': edited,
        'changes':   changes,
        'kept': kept,
        'kept_not': kept_not,
        'msgs': msgs,
    }
    return render_to_response('groups/group_change_officers.html', context, context_instance=RequestContext(request), )

@permission_required('groups.view_signatories')
def view_signatories(request, ):
    # TODO:
    # * limit which columns (roles) get displayed
    # This might want to wait for the generic reporting infrastructure, since
    # I'd imagine some of it can be reused.

    the_groups = groups.models.Group.objects.all()
    groups_filterset = GroupFilter(request.GET, the_groups)
    the_groups = groups_filterset.qs
    officers = groups.models.OfficeHolder.objects.filter(start_time__lte=datetime.datetime.now(), end_time__gte=datetime.datetime.now())
    officers = officers.filter(group__in=the_groups)
    officers = officers.select_related(depth=1)
    roles = groups.models.OfficerRole.objects.all()
    officers_map = collections.defaultdict(lambda: collections.defaultdict(set))
    for officer in officers:
        officers_map[officer.group][officer.role].add(officer.person)
    officers_data = []
    for group in the_groups:
        role_list = []
        for role in roles:
            role_list.append(officers_map[group][role])
        officers_data.append((group, role_list))

    context = {
        'roles': roles,
        'officers': officers_data,
        'filter': groups_filterset,
        'pagename': 'groups',
    }
    return render_to_response('groups/groups_signatories.html', context, context_instance=RequestContext(request), )

def search_groups(request, ):
    the_groups = groups.models.Group.objects.all()
    groups_filterset = GroupFilter(request.GET, the_groups)

    dest = None
    if 'signatories' in request.GET:
        dest = reverse('groups:signatories')
        print dest
    elif 'group-info' in request.GET:
        dest = reverse('groups:list')

    if dest:
        return redirect(dest + "?" + request.META['QUERY_STRING'])
    else:
        context = {
            'filter': groups_filterset,
            'pagename': 'groups',
        }
        return render_to_response('groups/group_search.html', context, context_instance=RequestContext(request), )


class GroupHistoryView(ListView):
    context_object_name = "version_list"
    template_name = "groups/group_version.html"

    def get_queryset(self):
        history_entries = None
        if 'pk' in self.kwargs:
            group = get_object_or_404(groups.models.Group, pk=self.kwargs['pk'])
            history_entries = reversion.models.Version.objects.get_for_object(group)
        else:
            history_entries = reversion.models.Version.objects.all()
            group_content_type = ContentType.objects.get_for_model(groups.models.Group)
            history_entries = history_entries.filter(content_type=group_content_type)
        length = len(history_entries)
        if length > 150:
            history_entries = history_entries[length-100:]
        return history_entries

    def get_context_data(self, **kwargs):
        context = super(GroupHistoryView, self).get_context_data(**kwargs)
        if 'pk' in self.kwargs:
            group = get_object_or_404(groups.models.Group, pk=self.kwargs['pk'])
            context['title'] = "History for %s" % (group.name, )
        else:
            context['title'] = "Recent Changes"
        return context


class AccountLookupForm(forms.Form):
    account_number = forms.IntegerField()
    username = forms.CharField(help_text="Athena username of person to check")

def account_lookup(request, ):
    msg = None
    msg_type = ""
    account_number = None
    username = None
    group = None
    office_holders = []

    visible_roles  = groups.models.OfficerRole.objects.filter(publicly_visible=True)

    initial = {}

    if 'search' in request.GET: # If the form has been submitted...
        # A form bound to the POST data
        form = AccountLookupForm(request.GET)

        if form.is_valid(): # All validation rules pass
            account_number = form.cleaned_data['account_number']
            username = form.cleaned_data['username']
            account_q = Q(main_account_id=account_number) | Q(funding_account_id=account_number)
            try:
                group = groups.models.Group.objects.get(account_q)
                office_holders = group.officers(person=username)
                office_holders = office_holders.filter(role__in=visible_roles)
            except groups.models.Group.DoesNotExist:
                msg = "Group not found"
                msg_type = "error"

    else:
        form = AccountLookupForm()

    context = {
        'username':     username,
        'account_number': account_number,
        'group':        group,
        'office_holders': office_holders,
        'form':         form,
        'msg':          msg,
        'msg_type':     msg_type,
        'visible_roles':    visible_roles,
    }
    return render_to_response('groups/account_lookup.html', context, context_instance=RequestContext(request), )
