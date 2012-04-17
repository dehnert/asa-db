# Create your views here.
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context, Template
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage, mail_admins
from django import forms
from django.forms import ValidationError
from django.db import connection
from django.db.models import Q
from django.utils.safestring import mark_safe

import django_filters

import groups.models
import space.models
import space.dump_locker_access
import space.dump_office_access

# Note: Not a view.
def process_access_changes(request, group, assignment, entries, changes, extras_indices, ):
    for entry in entries:
        key = "grant[%d][%d]" % (assignment.pk, entry.pk)
        if key in request.POST:
            pass
        else:
            changes.append(('Expire', assignment.space, entry))
            entry.expire()
    for index in extras_indices:
        key = "new[%d][%d]" % (assignment.pk, index)
        name = request.POST.get(key+"[name]", "")
        if name:
            entry = space.models.SpaceAccessListEntry(
                group=group,
                space=assignment.space,
            )
            entry.name = name
            entry.card_number = request.POST.get(key+"[card]", "")
            changes.append(('Add', assignment.space, entry))
            entry.save()

@login_required
def manage_access(request, pk, ):
    group = get_object_or_404(groups.models.Group, pk=pk)

    priv_view = request.user.has_perm('groups.view_group_private_info', group)
    priv_admin = request.user.has_perm('groups.admin_group', group)
    priv_rw = priv_admin
    if not (priv_view or priv_admin):
        raise PermissionDenied

    office_access = group.officers(role='office-access')
    locker_access = group.officers(role='locker-access')
    assignments = space.models.SpaceAssignment.current.filter(group=group)
    office_pairs = []
    locker_pairs = []
    changes = []
    if priv_rw:
        extras_indices = range(6)
    else:
        extras_indices = []
    if request.method == 'POST' and priv_rw:
        edited = True
    else:
        edited = False
    for assignment in assignments:
        entries = space.models.SpaceAccessListEntry.current.filter(group=group, space=assignment.space)
        if assignment.is_locker():
            pairs = locker_pairs
        else:
            pairs = office_pairs
        if edited:
            process_access_changes(
                request, group,
                assignment, entries.filter(),
                changes, extras_indices,
            )
        pair = (assignment, entries)
        pairs.append(pair)
    allow_edit = priv_rw and ((len(office_pairs) + len(locker_pairs)) > 0)
    context = {
        'group': group,
        'office': office_access,
        'locker': locker_access,
        'office_pairs': office_pairs,
        'locker_pairs': locker_pairs,
        'changes': changes,
        'allow_edit': allow_edit,
        'extras_indices': extras_indices,
        'pagename':'group',
    }
    return render_to_response('space/manage-access.html', context, context_instance=RequestContext(request), )

@permission_required('groups.view_group_private_info')
def dump_locker_access(request, ):
    response = HttpResponse(mimetype='text/csv')
    space_users = space.dump_locker_access.gather_users()
    space.dump_locker_access.print_info(space_users, response)
    return response

@permission_required('groups.view_group_private_info')
def dump_office_access(request, ):
    response = HttpResponse(mimetype='text/csv')
    space.dump_office_access.print_info(response)
    return response
