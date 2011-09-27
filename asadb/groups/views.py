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
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelChoiceField
from django.db import connection
from django.db.models import Q

import form_utils.forms
import reversion.models
import django_filters

from util.db_form_utils import StaticWidget



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

@permission_required('groups.add_group')
def create_group(request, status=None,):
    if not status: status = 'active'
    groupstatus = get_object_or_404(groups.models.GroupStatus, slug=status)
    
    change_restricted = False

    msg = None

    group = groups.models.Group()
    group.group_status = groupstatus
    group.recognition_date  = datetime.datetime.now()
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
            return redirect(reverse('groups:group-detail', args=[request_obj.pk]))
        else:
            msg = "Validation failed. See below for details."

    else:
        form = GroupChangeMainForm(change_restricted=change_restricted, instance=group, ) # An unbound form

    context = {
        'form':  form,
        'msg':   msg,
    }
    return render_to_response('groups/group_create.html', context, context_instance=RequestContext(request), )

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
