import forms.models
import groups.models
import settings

from django.views.generic import list_detail
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelChoiceField
from django.core.mail import send_mail, mail_admins
from django.template import Context, Template
from django.template.loader import get_template

import datetime

#################
# GENERIC VIEWS #
#################

class SelectGroupForm(Form):
    group = ModelChoiceField(queryset=groups.models.Group.objects.all())

def select_group(request, url_name_after, pagename='homepage', ):
    if request.method == 'POST': # If the form has been submitted...
        form = SelectGroupForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            group = form.cleaned_data['group'].id
            return HttpResponseRedirect(reverse(url_name_after, args=[group],)) # Redirect after POST
    else:
        form = SelectGroupForm() # An unbound form

    context = {
        'form':form,
        'pagename':'request_reimbursement',
    }
    return render_to_response('forms/select.html', context, context_instance=RequestContext(request), )

#############################
# FIRST-YEAR SUMMER MAILING #
#############################

def fysm_by_years(request, year, category, ):
    if year is None: year = datetime.date.today().year
    queryset = forms.models.FYSM.objects.filter(year=year).order_by('group__name')
    category_obj = None
    if category != None:
        category_obj = get_object_or_404(forms.models.FYSMTag, slug=category)
        queryset = queryset.filter(tags=category_obj)
    categories = forms.models.FYSMTag.objects.all()
    return list_detail.object_list(
        request,
        queryset=queryset,
        template_name="fysm/fysm_listing.html",
        template_object_name="fysm",
        extra_context={
            "year": year,
            "pagename": "fysm",
            "category": category_obj,
            "categories": categories,
        }
    )

class FYSMRequestForm(ModelForm):
    class Meta:
        model = forms.models.FYSM
        fields = (
            'display_name',
            'website',
            'join_url',
            'contact_email',
            'description',
            'logo',
            'tags',
        )

def fysm_manage(request, group, ):
    year = datetime.date.today().year
    group_obj = get_object_or_404(groups.models.Group, pk=group)

    initial = {}
    try:
        fysm_obj = forms.models.FYSM.objects.get(group=group_obj, year=year, )
        print "Successfully found", fysm_obj.__dict__
    except forms.models.FYSM.DoesNotExist:
        fysm_obj = forms.models.FYSM()
        fysm_obj.group = group_obj
        fysm_obj.year = year
        initial['display_name'] = group_obj.name
        initial['year'] = year
        initial['website'] = group_obj.website_url
        initial['join_url'] = group_obj.website_url
        initial['contact_email'] = group_obj.officer_email

    if request.method == 'POST': # If the form has been submitted...
        form = FYSMRequestForm(request.POST, request.FILES, instance=fysm_obj, ) # A form bound to the POST data

        if form.is_valid(): # All validation rules pass
            request_obj = form.save()

            # Send email
            tmpl = get_template('fysm/update_email.txt')
            ctx = Context({
                'group': group_obj,
                'fysm': fysm_obj,
                'submitter': request.user,
                'request': request,
                'sender': "ASA FYSM team",
            })
            body = tmpl.render(ctx)
            recipients = ['asa-fysm@mit.edu', group_obj.officer_email, ]
            send_mail(
                'FYSM entry for "%s" updated by "%s"' % (
                    group_obj.name,
                    request.user,
                ),
                body,
                'asa-fysm@mit.edu',
                recipients,
            )
            return HttpResponseRedirect(reverse('fysm-thanks', args=[fysm_obj.pk],)) # Redirect after POST

    else:
        form = FYSMRequestForm(instance=fysm_obj, initial=initial, ) # An unbound form

    context = {
        'group':group_obj,
        'fysm':fysm_obj,
        'form':form,
        'pagename':'fysm',
    }
    return render_to_response('fysm/submit.html', context, context_instance=RequestContext(request), )


def fysm_thanks(request, fysm, ):
    year = datetime.date.today().year
    fysm_obj = get_object_or_404(forms.models.FYSM, pk=fysm)

    context = {
        'group':fysm_obj.group,
        'fysm':fysm_obj,
        'pagename':'fysm',
    }
    return render_to_response('fysm/thanks.html', context, context_instance=RequestContext(request), )
