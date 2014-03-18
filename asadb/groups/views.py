# Create your views here.

import collections
import csv
import datetime

from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator, EmailValidator, email_re
from django.core.mail import EmailMessage, mail_admins
from django import forms
from django.forms import ValidationError
from django.db import connection
from django.db.models import Q
from django.utils import html
from django.utils.safestring import mark_safe

import form_utils.forms
import reversion.models
import django_filters

import groups.models
from util.db_form_utils import StaticWidget
import util.db_filters
from util.emails import email_from_template

urlvalidator = URLValidator()
emailvalidator = EmailValidator(email_re)



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

def view_roles_descriptions(request, ):
    roles  = groups.models.OfficerRole.objects.all()
    context = {
        'pagename': 'about',
        'roles': roles,
    }
    return render_to_response('about/roles_descriptions.html', context, context_instance=RequestContext(request), )

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
        context['pagename'] = "groups"

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
        context['my_roles'] = []
        if self.request.user.is_authenticated():
            context['my_roles'] = group.officers(person=self.request.user.username).select_related('role')

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
        for field in self.force_required:
            self.fields[field].required = True
        self.fields['constitution_url'].help_text = mark_safe("Please put your current constitution URL or AFS path.")

    exec_only_fields = [
        'name', 'abbreviation',
        'group_status', 'group_class',
        'group_funding', 'main_account_id', 'funding_account_id',
    ]
    nobody_fields = [
        'recognition_date',
    ]
    force_required = [
        'activity_category', 'description',
        'num_undergrads', 'num_grads', 'num_community', 'num_other',
        'website_url', 'officer_email', 'group_email',
        'constitution_url', 'athena_locker',
    ]


    class Meta:
        fieldsets = [
            ('basic', {
                'legend': 'Basic Information',
                'fields': ['name', 'abbreviation', 'activity_category', 'description', ],
            }),
            ('size', {
                'legend':'Membership Numbers',
                'description':'Count each person in your group exactly once. Count only MIT students as "undergrads" or "grads". "Community" should be MIT community members who are not students, such as alums and staff.',
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

@login_required
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
        'pagename': "groups",
    }
    return render_to_response('groups/group_change_main.html', context, context_instance=RequestContext(request), )

# Helper for manage_officers view
def manage_officers_load_officers(group, ):
    officers = group.officers()
    people = sorted(set([ officer.person for officer in officers ]))
    roles  = groups.models.OfficerRole.objects.all()

    name_map = {}
    for name in people:
        name_map[name] = groups.models.AthenaMoiraAccount.try_format_by_username(name)
    officers_map = {}

    for officer in officers:
        officers_map[(officer.person, officer.role)] = officer

    return people, roles, name_map, officers_map

# Helper for manager_officers view
def manage_officers_load_accounts(max_new, people, request, msgs, ):
    new_people = {}
    moira_accounts = {}

    for i in range(max_new):
        key = "extra.%d" % (i, )
        if key in request.POST and request.POST[key] != "":
            username = request.POST[key]

            local, at, domain = username.partition('@')
            if at and domain.lower() == 'mit.edu':
                msgs.append('In general, you should specify just the Athena username (for example, %s), not the whole email address (like %s).' % (local, username))
                username = local

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

    return new_people, moira_accounts

# Helper for manager_officers view
def manage_officers_sync_role_people(
    group, role, new_holders,
    msgs, changes,
    officers_map, people, moira_accounts, new_people, max_new, ):
    """
    Sync a set of new holders of a role with the database.

    Arguments:
    Function-specific:
        role: the role object the changes center around
        new_holders: The desired final set of people who should have the role
    Output arguments --- information messages
        msgs: warning message list. Output argument.
        changes: list of changes made. [(verb, color, person, role)]
    Background info arguments:
        officers_map: (username, role) -> OfficeHolder
        people: list of all potentially-affected people (who were previously involved)
        moira_accounts: username -> AthenaMoiraAccount
        new_people: potentially-affected people (who are newly involved) --- key -> username
        max_new: highest index to use in keys for new_people
    """

    kept = 0
    kept_not = 0

    for person in people:
        if person in new_holders:
            if (person, role) in officers_map:
                if person not in moira_accounts:
                    pass # already errored above
                elif role.require_student and not moira_accounts[person].is_student():
                    msgs.append('Only students can have the %s role, and %s does not appear to be a student. (If this is not the case, please contact us.) You should replace this person ASAP.' % (role, person, ))
                #changes.append(("Kept", "yellow", person, role))
                kept += 1
            else:
                if person not in moira_accounts:
                    pass # already errored above
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
                assert person in moira_accounts
                if role.require_student and not moira_accounts[person].is_student():
                    msgs.append('Only students can have the %s role, and %s does not appear to be a student.' % (role, person, ))
                else:
                    holder = groups.models.OfficeHolder(person=person, role=role, group=group,)
                    holder.save()
                    changes.append(("Added", "green", person, role))

    return kept, kept_not

# Helper for manager_officers view
def manage_officers_table_update(
    group,
    request, context, msgs, changes,
    people, roles, officers_map, max_new, ):

    context['kept'] = 0
    context['kept_not'] = 0

    # Fill out moira_accounts with AthenaMoiraAccount objects for relevant people
    new_people, moira_accounts = manage_officers_load_accounts(max_new, people, request, msgs)

    # Process changes
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
            kept_delta, kept_not_delta = manage_officers_sync_role_people(
                group, role, new_holders,   # input arguments
                msgs, changes,              # output arguments
                officers_map, people, moira_accounts,   # ~background data
                new_people, max_new,                    # new people data
            )
            context['kept'] += kept_delta
            context['kept_not'] += kept_not_delta


class OfficersBulkManageForm(forms.Form):
    mode_choices = [
        ('add', 'Add new people', ),
        ('remove', 'Remove old people', ),
        ('sync', 'Set people to list provided', ),
    ]
    mode_help = '"Set people to list provided" will add people not listed in the grid above, and remove people not listed in the textbox below. You must always specify at least one username, and thus cannot use "Set people" to remove all people.'
    mode = forms.ChoiceField(choices=mode_choices, help_text=mode_help, )
    role = forms.ChoiceField(initial='office-access', )
    people = forms.CharField(
        help_text='Usernames of people, one per line.',
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
        self._roles = kwargs['roles']
        del kwargs['roles']
        super(OfficersBulkManageForm, self).__init__(*args, **kwargs)
        role_choices = [ (role.slug, role.display_name) for role in self._roles ]
        self.fields['role'].choices = role_choices

    def get_role(self, ):
        role_slug = self.cleaned_data['role']
        for role in self._roles:
            if role.slug == role_slug:
                return role
        raise groups.OfficerRole.DoesNotExist

def manage_officers_bulk_update(
        group, bulk_form,
        msgs, changes,
        officers_map, ):

    # Load parameters
    mode = bulk_form.cleaned_data['mode']
    role = bulk_form.get_role()
    people_lst = bulk_form.cleaned_data['people'].split('\n')
    people_set = set([p.strip() for p in people_lst])
    if '' in people_set: people_set.remove('')

    # Fill out moira_accounts
    moira_accounts = {}
    for username in people_set:
        try:
            moira_accounts[username] = groups.models.AthenaMoiraAccount.active_accounts.get(username=username)
        except groups.models.AthenaMoiraAccount.DoesNotExist:
            msgs.append('Athena account "%s" appears not to exist. Changes involving them have been ignored.' % (username, ))

    # Find our target sets
    cur_holders = [user for user, map_role in officers_map if role == map_role]
    people = people_set.union(cur_holders)
    if mode == 'add':
        new_holders = people
    elif mode == 'remove':
        new_holders = people-people_set
    elif mode == 'sync':
        new_holders = people_set
    else:
        raise NotImplementedError("Unknown operation '%s'" % (mode, ))

    # Make changes
    if len(new_holders) <= role.max_count:
        new_people = dict()
        max_new = 0
        manage_officers_sync_role_people(
            group, role, new_holders,
            msgs, changes,
            officers_map, people, moira_accounts, new_people, max_new,
        )
    else:
        too_many_tmpl = "You selected %d people for %s; only %d are allowed. No changes have been made in this update."
        error = too_many_tmpl % (len(new_holders), role.display_name, role.max_count, )
        msgs.append(error)

@login_required
def manage_officers(request, pk, ):
    group = get_object_or_404(groups.models.Group, pk=pk)

    if not request.user.has_perm('groups.admin_group', group):
        raise PermissionDenied

    people, roles, name_map, officers_map = manage_officers_load_officers(group)

    max_new = 4
    msgs = []
    changes = []

    context = {
        'group': group,
        'roles': roles,
        'people': people,
        'changes':   changes,
        'msgs': msgs,
    }

    if request.method == 'POST' and 'opt-mode' in request.POST: # If the form has been submitted
        edited = True

        # Do the changes
        if request.POST['opt-mode'] == 'table':
            context['bulk_form'] = OfficersBulkManageForm(roles=roles, )
            manage_officers_table_update(
                group,
                request, context, msgs, changes,
                people, roles, officers_map, max_new,
            )
        elif request.POST['opt-mode'] == 'bulk':
            bulk_form = OfficersBulkManageForm(request.POST, roles=roles, )
            context['bulk_form'] = bulk_form
            if bulk_form.is_valid():
                manage_officers_bulk_update(
                    group, bulk_form,
                    msgs, changes,
                    officers_map, )
        else:
            raise NotImplementedError("Update mode must be table or bulk, was '%s'" % (request.POST['opt-mode'], ))

        # mark as changed and reload the data
        if changes:
            group.set_updater(request.user)
            group.save()
        people, roles, name_map, officers_map = manage_officers_load_officers(group)
    else:
        context['bulk_form'] = OfficersBulkManageForm(roles=roles, )

    officers_data = []
    for person in people:
        role_list = []
        for role in roles:
            if (person, role) in officers_map:
                role_list.append((role, True))
            else:
                role_list.append((role, False))
        officers_data.append((False, person, name_map[person], role_list))
    null_role_list = [(role, False) for role in roles]
    for i in range(max_new):
        officers_data.append((True, "extra.%d" % (i, ), "", null_role_list))
    context['officers'] = officers_data
    context['pagename'] = "groups"

    return render_to_response('groups/group_change_officers.html', context, context_instance=RequestContext(request), )



##################
# ACCOUNT LOOKUP #
##################

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
    def clean_president_kerberos(self, ):
        username = self.cleaned_data['president_kerberos']
        validate_athena(username, True, )
        return username

    def clean_treasurer_kerberos(self, ):
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
        self.fields['group_email'].required = True
        self.fields['athena_locker'].required = True
        self.fields['athena_locker'].help_text = "In general, this is limited to twelve characters. You should stick to letters, numbers, and hyphens. (Underscores and dots are also acceptable, but may cause problems in some situations.)"

        # Specifically, if the group ends up wanting to use scripts.mit.edu,
        # they will currently be assigned locker.scripts.mit.edu. If they try
        # to use foo.bar, then https://foo.bar.scripts.mit.edu/ will produce a
        # certificate name mismatch. Officially, underscores are not allowed in
        # hostnames, so foo_.scripts.mit.edu may fail with some software.

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
            officer_emails = create_group_officers(group, form.cleaned_data, save=True, )

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

@login_required
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

def review_group_check_warnings(group_startup, group, ):
    warnings = []

    if group.name.startswith("MIT "):
        warnings.append('Group name starts with "MIT". Generally, we prefer "Foo, MIT" instead.')
    if "mit" in group.athena_locker.lower():
        warnings.append('Athena locker name contains "mit", which may be redundant with paths like "http://web.mit.edu/mitfoo" or "/mit/foo/".')

    if group_startup.president_kerberos == group_startup.treasurer_kerberos:
        warnings.append('President matches Treasurer.')
    if "%s@mit.edu" % (group_startup.president_kerberos, ) in (group.officer_email, group.group_email):
        warnings.append('President email matches officer and/or group email.')
    if group.officer_email == group.group_email:
        warnings.append('Officer email matches group email.')

    if '@mit.edu' not in group.officer_email or '@mit.edu' not in group.group_email:
        warnings.append('Officer and/or group email are non-MIT. Ensure that they are not requesting the addresses be created, and consider suggesting they use an MIT list instead.')

    if '.' in group.athena_locker:
        warnings.append('Athena locker contains a ".". This is not compatible with scripts.mit.edu\'s wildcard certificate, and may cause other problems.')
    if '_' in group.athena_locker:
        warnings.append('Athena locker contains a "_". If this locker name gets used in a URL (for example, locker.scripts.mit.edu), it will technically violate the hostname specification and may not work in some clients.')
    if len(group.athena_locker) > 12:
        warnings.append('Athena locker is more than twelve characters long. In general, twelve characters is the longest Athena locker an ASA-recognized group can get.')

    return warnings

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

    context['warnings'] = review_group_check_warnings(group_startup, group)

    context['msg'] = ""
    if request.method == 'POST':
        if 'approve' in request.POST:
            group_startup.stage = groups.models.GROUP_STARTUP_STAGE_APPROVED
            group_startup.save()

            group.group_status = groups.models.GroupStatus.objects.get(slug='suspended')
            group.constitution_url = ""
            group.recognition_date = datetime.datetime.now()
            group.set_updater(request.user)

            note = groups.models.GroupNote(
                author=request.user.username,
                body="Approved group for recognition.",
                acl_read_group=True,
                acl_read_offices=True,
                group=group,
            ).save()

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
    officer_email = django_filters.CharFilter(lookup_type='icontains', label="Officers' list contains")

    account_filter = util.db_filters.MultiNumberFilter(
        lookup_type='exact', label="Account number",
        names=('main_account_id', 'funding_account_id', ),
    )

    class Meta:
        model = groups.models.Group
        fields = [
            'name',
            'abbreviation',
            'officer_email',
            'activity_category',
            'group_class',
            'group_status',
            'group_funding',
            'account_filter',
        ]

    def __init__(self, data=None, *args, **kwargs):
        if not data: data = None
        super(GroupFilter, self).__init__(data, *args, **kwargs)
        active_pk = groups.models.GroupStatus.objects.get(slug='active').pk
        self.form.initial['group_status'] = active_pk


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


@permission_required('groups.view_signatories')
def view_signatories(request, ):
    the_groups = groups.models.Group.objects.all()
    groups_filterset = GroupFilter(request.GET, the_groups)
    the_groups = groups_filterset.qs

    officers = groups.models.OfficeHolder.objects.filter(start_time__lte=datetime.datetime.now(), end_time__gte=datetime.datetime.now())
    officers = officers.filter(group__in=the_groups)
    officers = officers.select_related(depth=1)

    role_slugs = ['president', 'treasurer', 'financial', 'reservation']
    roles = groups.models.OfficerRole.objects.filter(slug__in=role_slugs)
    roles = sorted(roles, key=lambda r: role_slugs.index(r.slug))

    officers_map = collections.defaultdict(lambda: collections.defaultdict(set))
    for officer in officers:
        officers_map[officer.group][officer.role].add(officer.person)
    officers_data = []
    for group in the_groups:
        role_list = []
        for role in roles:
            role_list.append(sorted(officers_map[group][role]))
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
    elif 'group-goto' in request.GET:
        if len(groups_filterset.qs) == 1:
            group = groups_filterset.qs[0]
            return redirect(reverse('groups:group-detail', kwargs={'pk':group.pk}))
        else:
            dest = reverse('groups:list')
    elif 'group-list' in request.GET:
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
            history_entries = reversion.get_for_object(group)
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
            context['adminpriv'] = self.request.user.has_perm('groups.admin_group', group)
            context['group'] = group
        else:
            context['title'] = "Recent Changes"
        context['pagename'] = 'groups'
        return context


@permission_required('groups.view_group_private_info')
def downloaded_constitutions(request, ):
    constitutions = groups.models.GroupConstitution.objects
    constitutions = constitutions.order_by('failure_reason', 'status_msg', 'failure_date', 'group__name', ).select_related('group', 'group__group_status', )
    failures = collections.defaultdict(list)
    successes = collections.defaultdict(list)
    for const in constitutions:
        if const.failure_reason:
            failures[const.failure_reason].append(const)
        else:
            successes[const.status_msg].append(const)
    context = {}
    context['failures']  = sorted(failures.items(),  key=lambda x: x[0])
    context['successes'] = sorted(successes.items(), key=lambda x: x[0])
    context['pagename'] = 'groups'
    return render_to_response('groups/groups_constitutions.html', context, context_instance=RequestContext(request), )


@permission_required('groups.view_group_private_info')
def downloaded_constitutions_csv(request, ):
    active_groups = groups.models.Group.active_groups.all()
    constitutions = groups.models.GroupConstitution.objects.filter(group__in=active_groups)
    constitutions = constitutions.order_by('failure_reason', 'status_msg', 'failure_date', 'group__name', ).select_related('group', 'group__group_status')

    response = HttpResponse(mimetype='text/csv')
    writer = csv.writer(response)

    writer.writerow([
        'failure_date',
        'status_msg',
        'name', 'id', 'group_status', 'email',
        'constitution_url',
    ])
    for const in constitutions:
        writer.writerow([
            const.failure_date,
            const.status_msg.strip(),
            const.group.name,
            const.group.pk,
            const.group.group_status.slug,
            const.group.officer_email,
            const.source_url,
        ])
    return response



#######################
# REPORTING COMPONENT #
#######################

name_formats = collections.OrderedDict()
name_formats['username']    = ('username',                      False,  '%(user)s')
name_formats['email']       = ('username@mit.edu',              False,  '%(user)s@mit.edu')
name_formats['name']        = ('First Last',                    True,   '%(first)s %(last)s')
name_formats['name-email']  = ('First Last <username@mit.edu>', True,   '%(first)s %(last)s <%(user)s@mit.edu>')

class ReportingForm(form_utils.forms.BetterForm):
    special_filters = forms.fields.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={'size': 10}),
        validators=[groups.models.filter_registry.validate_filter_slug],
        required=False,
    )

    basic_fields_choices = groups.models.Group.reporting_fields()
    basic_fields_labels = dict(basic_fields_choices) # name -> verbose_name
    basic_fields = forms.fields.MultipleChoiceField(
        choices=basic_fields_choices,
        widget=forms.CheckboxSelectMultiple,
        initial = ['id', 'name'],
    )

    people_fields = forms.models.ModelMultipleChoiceField(
        queryset=groups.models.OfficerRole.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    name_format = forms.ChoiceField(
        help_text='How to format the names of the President, Treasurer, etc., if displayed',
        choices=[(k, v[0]) for k,v in name_formats.items()],
        initial='username',
        required=True,
    )

    special_fields_choices = (
        ('option_entry', '<option> entry', ),
    )
    special_fields = forms.fields.MultipleChoiceField(
        choices=special_fields_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    _format_choices = [
        ('html/inline',     "Web (HTML)", ),
        ('csv/inline',      "Spreadsheet (CSV) --- in browser", ),
        ('csv/download',    "Spreadsheet (CSV) --- download", ),
    ]
    output_format = forms.fields.ChoiceField(choices=_format_choices, widget=forms.RadioSelect, initial='html/inline')

    class Meta:
        fieldsets = [
            ('filter', {
                'legend': 'Filter Groups',
                'fields': [
                    'name', 'abbreviation',
                    'activity_category', 'group_class', 'group_status', 'group_funding',
                    'special_filters',
                ],
            }),
            ('fields', {
                'legend': 'Data to display',
                'fields': ['basic_fields', 'people_fields', 'name_format', 'special_fields', ],
            }),
            ('final', {
                'legend': 'Final options',
                'fields': ['o', 'output_format', ],
            }),
        ]

    def __init__(self, *args, **kwargs):
        super(ReportingForm, self).__init__(*args, **kwargs)

        registry = groups.models.filter_registry
        self.fields['special_filters'].choices = registry.get_choices()

class GroupReportingFilter(GroupFilter):
    class Meta(GroupFilter.Meta):
        form = ReportingForm
        order_by = True # we customize the field, so the value needs to be true-like but doesn't matter otherwise

    def get_ordering_field(self):
        return forms.ChoiceField(label="Ordering", required=False, choices=ReportingForm.basic_fields_choices)

    def __init__(self, data=None, *args, **kwargs):
        super(GroupReportingFilter, self).__init__(data, *args, **kwargs)

def format_id(pk):
    url = reverse('groups:group-detail', kwargs={'pk':pk})
    return mark_safe("<a href='%s'>%d</a>" % (url, pk))

def format_url(url):
    try:
        urlvalidator(url)
    except ValidationError:
        return url
    else:
        escaped = html.escape(url)
        return mark_safe("<a href='%s'>%s</a>" % (escaped, escaped))

def format_email(email):
    try:
        emailvalidator(email)
    except ValidationError:
        return email
    else:
        escaped = html.escape(email)
        return mark_safe("<a href='mailto:%s'>%s</a>" % (escaped, escaped))

def format_option_entry(group):
    name = html.escape(group.name)
    return '<option value="%s">%s</option>' % (name, name, )

reporting_html_formatters = {
    'id': format_id,
    'website_url': format_url,
    'constitution_url': format_url,
    'group_email': format_email,
    'officer_email': format_email,
}

@permission_required('groups.view_group_private_info')
def reporting(request, ):
    the_groups = groups.models.Group.objects.all()
    groups_filterset = GroupReportingFilter(request.GET, the_groups)
    form = groups_filterset.form

    col_labels = []
    report_groups = []
    run_report = 'go' in request.GET and form.is_valid()
    if run_report:
        basic_fields = form.cleaned_data['basic_fields']
        output_format, output_disposition = form.cleaned_data['output_format'].split('/')
        col_labels = [form.basic_fields_labels[field] for field in basic_fields]

        # Set up query
        qs = groups_filterset.qs
        for fltr_slug in form.cleaned_data['special_filters']:
            fltr = groups.models.filter_registry.get(fltr_slug)
            qs = qs.filter(pk__in=fltr.queryset())

        # Prefetch foreign keys
        prefetch_fields = groups.models.Group.reporting_prefetch()
        prefetch_fields = prefetch_fields.intersection(basic_fields)
        if prefetch_fields:
            qs = qs.select_related(*list(prefetch_fields))

        # Set up people
        people_fields = form.cleaned_data['people_fields']
        people_data = groups.models.OfficeHolder.current_holders.filter(group__in=qs, role__in=people_fields)
        # Group.pk -> (OfficerRole.pk -> set(username))
        people_map = collections.defaultdict(lambda: collections.defaultdict(set))
        for holder in people_data:
            people_map[holder.group_id][holder.role_id].add(holder.person)
        for field in people_fields:
            col_labels.append(field.display_name)
        # Figure out the format, and if necessary fetch human names
        nf_slug = form.cleaned_data['name_format']
        nf_label, nf_need_name, nf_fmt = name_formats[nf_slug]
        name_map = collections.defaultdict(lambda: ('???', '???'))
        if nf_need_name:
            people_usernames = [p.person.lower() for p in people_data]
            name_data = groups.models.AthenaMoiraAccount.objects.filter(username__in=people_usernames)
            for account in name_data:
                name_map[account.username.lower()] = (account.first_name, account.last_name)

        # Set up special fields
        special_formatters = []
        if 'option_entry' in form.cleaned_data['special_fields']:
            col_labels.append('option_entry')
            special_formatters.append(format_option_entry)

        # Assemble data
        if output_format == 'html':
            formatters = reporting_html_formatters
        else:
            formatters = {}
        def fetch_item(group, field):
            val = getattr(group, field)
            if field in formatters:
                val = formatters[field](val)
            return val

        for group in qs:
            group_data = [fetch_item(group, field) for field in basic_fields]
            for field in people_fields:
                people = people_map[group.pk][field.pk]
                if nf_need_name:
                    def fmt(p):
                        first, last = name_map[p.lower()]
                        ctx = {'user': p, 'first': first, 'last': last}
                        return nf_fmt % ctx
                    people = [fmt(p) for p in people]
                else:
                    people = [nf_fmt % {'user': p} for p in people]
                group_data.append(", ".join(people))

            for formatter in special_formatters:
                group_data.append(formatter(group))

            report_groups.append(group_data)

        # Handle output as CSV
        if output_format == 'csv':
            if output_disposition == 'download':
                mimetype = 'text/csv'
            else:
                # Firefox, at least, downloads text/csv regardless
                mimetype = 'text/plain'
            response = HttpResponse(mimetype=mimetype)
            if output_disposition == 'download':
                response['Content-Disposition'] = 'attachment; filename=asa-db-report.csv'
            writer = csv.writer(response)
            writer.writerow(col_labels)
            for row in report_groups:
                utf8_row = [unicode(cell).encode("utf-8") for cell in row]
                writer.writerow(utf8_row)
            return response

    # Handle output as HTML
    context = {
        'form': form,
        'run_report': run_report,
        'column_labels': col_labels,
        'report_groups': report_groups,
        'pagename': 'groups',
    }
    return render_to_response('groups/reporting.html', context, context_instance=RequestContext(request), )


@permission_required('groups.view_group_private_info')
def show_nonstudent_officers(request, ):
    student_roles  = groups.models.OfficerRole.objects.filter(require_student=True, )
    student_q = groups.models.AthenaMoiraAccount.student_q()
    students = groups.models.AthenaMoiraAccount.active_accounts.filter(student_q)
    office_holders = groups.models.OfficeHolder.current_holders.order_by('group__name', 'role', )
    office_holders = office_holders.filter(role__in=student_roles)
    office_holders = office_holders.exclude(person__in=students.values('username'))
    office_holders = office_holders.select_related('group', 'group__group_status', 'role')

    msg = None
    msg_type = ""
    if 'sort' in request.GET:
        if request.GET['sort'] == 'group':
            office_holders = office_holders.order_by('group__name', 'group__group_status', 'role', 'person', )
        elif request.GET['sort'] == 'status':
            office_holders = office_holders.order_by('group__group_status', 'group__name', 'role', 'person', )
        elif request.GET['sort'] == 'role':
            office_holders = office_holders.order_by('role', 'group__group_status', 'group__name', 'person', )
        elif request.GET['sort'] == 'person':
            office_holders = office_holders.order_by('person', 'group__group_status', 'group__name', 'role', )
        else:
            msg = 'Unknown sort key "%s".' % (request.GET['sort'], )
            msg_type = 'error'

    context = {
        'pagename': 'groups',
        'roles': student_roles,
        'holders': office_holders,
        'msg': msg,
        'msg_type': msg_type,
    }

    return render_to_response('groups/reporting/non-students.html', context, context_instance=RequestContext(request), )


