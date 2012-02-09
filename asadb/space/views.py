# Create your views here.
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context, Template
from django.http import Http404, HttpResponseRedirect
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

def view_access(request, pk, ):
    group = get_object_or_404(groups.models.Group, pk=pk)
    if not request.user.has_perm('groups.admin_group', group):
        raise PermissionDenied
    office_access = group.officers(role='office-access')
    locker_access = group.officers(role='locker-access')
    assignments = space.models.SpaceAssignment.current.filter(group=group)
    office_pairs = []
    locker_pairs = []
    for assignment in assignments:
        entries = space.models.SpaceAccessListEntry.current.filter(group=group, space=assignment.space)
        pair = (assignment, entries)
        if assignment.is_locker():
            locker_pairs.append(pair)
        else:
            office_pairs.append(pair)
    context = {
        'group': group,
        'office': office_access,
        'locker': locker_access,
        'office_pairs': office_pairs,
        'locker_pairs': locker_pairs,
        'pagename':'group',
    }
    return render_to_response('space/view-access.html', context, context_instance=RequestContext(request), )
