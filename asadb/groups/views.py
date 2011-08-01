# Create your views here.

import groups.models

from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage, mail_admins
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelChoiceField
from django.db.models import Q

import form_utils.forms
import reversion.models

class GroupChangeMainForm(form_utils.forms.BetterModelForm):
    class Meta:
        fieldsets = [
            ('basic', {
                'legend': 'Basic Information',
                'fields': ['name', 'abbreviation', 'description', 'activity_category', ],
            }),
            ('size', {
                'legend':'Membership Numbers',
                'fields': ['num_undergrads', 'num_grads', 'num_community', 'num_other',],
            }),
            ('contact', {
                'legend': 'Contact Information',
                'fields': ['website_url', 'meeting_times', 'group_email', 'officer_email', ],
            }),
            ('more-info', {
                'legend': 'Additional Information',
                'fields': ['constitution_url', 'advisor_name', 'main_account_id', 'funding_account_id', 'athena_locker', 'recognition_date', ],
            }),
        ]
        model = groups.models.Group

def manage_main(request, group_id, ):
    group = get_object_or_404(groups.models.Group, pk=group_id)

    if not request.user.has_perm('groups.change_group', group):
        raise PermissionDenied

    msg = None

    initial = {}
    if request.method == 'POST': # If the form has been submitted...
        form = GroupChangeMainForm(request.POST, request.FILES, instance=group, ) # A form bound to the POST data

        if form.is_valid(): # All validation rules pass
            request_obj = form.save()

            # Send email
            #tmpl = get_template('fysm/update_email.txt')
            #ctx = Context({
            #    'group': group_obj,
            #    'fysm': fysm_obj,
            #    'view_uri': view_uri,
            #    'submitter': request.user,
            #    'request': request,
            #    'sender': "ASA FYSM team",
            #})
            #body = tmpl.render(ctx)
            #email = EmailMessage(
            #    subject='FYSM entry for "%s" updated by "%s"' % (
            #        group_obj.name,
            #        request.user,
            #    ),
            #    body=body,
            #    from_email='asa-fysm@mit.edu',
            #    to=[group_obj.officer_email, request.user.email, ],
            #    bcc=['asa-fysm-submissions@mit.edu', ]
            #)
            #email.send()
            msg = "Thanks for editing!"

    else:
        form = GroupChangeMainForm(instance=group, initial=initial, ) # An unbound form

    context = {
        'group': group,
        'form':  form,
        'msg':   msg,
    }
    return render_to_response('groups/group_change_main.html', context, context_instance=RequestContext(request), )

class GroupDetailView(DetailView):
    context_object_name = "group"
    model = groups.models.Group
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        group = context['group']

        # Indicate whether this person should be able to see "private" info
        context['viewpriv'] = self.request.user.has_perm('groups.view_group_private_info', group)
        return context

class GroupHistoryView(ListView):
    context_object_name = "version_list"
    template_name = "groups/group_version.html"

    def get_queryset(self):
        history_entries = None
        if 'group' in self.kwargs:
            group = get_object_or_404(groups.models.Group, pk=self.kwargs['group'])
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
        if 'group' in self.kwargs:
            group = get_object_or_404(groups.models.Group, pk=self.kwargs['group'])
            context['title'] = "History for %s" % (group.name, )
        else:
            context['title'] = "Recent Changes"
        return context


def load_officers(group, ):
    officers = group.officers()
    people = list(set([ officer.person for officer in officers ]))
    roles  = groups.models.OfficerRole.objects.all()

    officers_map = {}
    for officer in officers:
        officers_map[(officer.person, officer.role)] = officer

    return people, roles, officers_map

def manage_officers(request, group_id, ):
    group = get_object_or_404(groups.models.Group, pk=group_id)

    if not request.user.has_perm('groups.change_group', group):
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
        for i in range(max_new):
            key = "extra.%d" % (i, )
            if key in request.POST:
                # TODO: validate as real usernames
                new_people[i] = request.POST[key]
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
                        # TODO: validate student status of appropriate officers
                        if (person, role) in officers_map:
                            #changes.append(("Kept", "yellow", person, role))
                            kept += 1
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
                            holder = groups.models.OfficeHolder(person=person, role=role, group=group,)
                            holder.save()
                            changes.append(("Added", "green", person, role))

        # reload the data
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
