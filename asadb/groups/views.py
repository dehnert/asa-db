# Create your views here.

import groups.models

from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import PermissionDenied
from django.views.generic import list_detail
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
                'fields': ['website_url', 'meeting_times', 'group_email', 'officer_email', 'athena_locker', ],
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
