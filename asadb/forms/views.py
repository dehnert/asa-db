import forms.models
import groups.models
import settings

from django.contrib.auth.decorators import user_passes_test, login_required
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

import datetime

#################
# GENERIC VIEWS #
#################

class SelectGroupForm(Form):
    group = ModelChoiceField(queryset=groups.models.Group.objects.all())
    def __init__(self, *args, **kwargs):
        queryset = None
        if 'queryset' in kwargs:
            queryset = kwargs['queryset']
            del kwargs['queryset']
        super(SelectGroupForm, self).__init__(*args, **kwargs)
        if queryset is not None:
            self.fields["group"].queryset = queryset

def select_group(request, url_name_after, pagename='homepage', queryset=None, ):
    if request.method == 'POST': # If the form has been submitted...
        # A form bound to the POST data
        form = SelectGroupForm(request.POST, queryset=queryset, )
        if form.is_valid(): # All validation rules pass
            group = form.cleaned_data['group'].id
            return HttpResponseRedirect(reverse(url_name_after, args=[group],)) # Redirect after POST
    else:
        form = SelectGroupForm(queryset=queryset, ) # An unbound form

    context = {
        'form':form,
        'pagename':pagename,
    }
    return render_to_response('forms/select.html', context, context_instance=RequestContext(request), )

#############################
# FIRST-YEAR SUMMER MAILING #
#############################

@login_required
def fysm_by_years(request, year, category, ):
    if year is None: year = datetime.date.today().year
    queryset = forms.models.FYSM.objects.filter(year=year).order_by('group__name')
    category_obj = None
    category_name = 'main'
    if category != None:
        category_obj = get_object_or_404(forms.models.FYSMCategory, slug=category)
        category_name = category_obj.name
        queryset = queryset.filter(categories=category_obj)
    forms.models.FYSMView.record_metric(request=request, fysm=None, year=year, page=category_name, )
    categories = forms.models.FYSMCategory.objects.all()
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

@login_required
def fysm_view(request, year, submission, ):
    submit_obj = get_object_or_404(forms.models.FYSM, pk=submission,)
    all = forms.models.FYSM.objects.only("id", "display_name", )
    try:
        prev = all.filter(display_name__lt=submit_obj.display_name).order_by("-display_name")[0]
    except IndexError:
        prev = None
    try:
        next = all.filter(display_name__gt=submit_obj.display_name).order_by("display_name")[0]
    except IndexError:
        next = None
    forms.models.FYSMView.record_metric(request=request, fysm=submit_obj, year=year, page="detail", )
    return list_detail.object_detail(
        request,
        forms.models.FYSM.objects,
        object_id=submission,
        template_name="fysm/fysm_detail.html",
        template_object_name="fysm",
        extra_context={
            "year": year,
            "pagename": "fysm",
            "prev": prev,
            "next": next,
        },
    )

def fysm_link(request, year, link_type, submission, ):
    submit_obj = get_object_or_404(forms.models.FYSM, pk=submission,)
    if submit_obj.year != int(year):
        raise Http404("Year mismatch: fysm.year='%s', request's year='%s'" % (submit_obj.year, year, ))
    if link_type == 'join':
        url = submit_obj.join_url
    elif link_type == 'website':
        url = submit_obj.website
    else:
        raise Http404("Unknown link type")
    forms.models.FYSMView.record_metric(request=request, fysm=submit_obj, year=year, page=link_type, )
    return HttpResponseRedirect(url)

def select_group_fysm(request, ):
    qobj = Q(activity_category__isnull = True) | ~(Q(activity_category__name='Dorm') | Q(activity_category__name='FSILG'))
    queryset = groups.models.Group.active_groups.filter(qobj)
    return select_group(
        request,
        url_name_after='fysm-manage',
        pagename='fysm',
        queryset=queryset,
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
            'slide',
            'tags',
            'categories',
        )

@login_required
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

            view_path = reverse('fysm-view', args=[year, request_obj.pk, ])
            view_uri = '%s://%s%s' % (request.is_secure() and 'https' or 'http',
                 request.get_host(), view_path)

            # Send email
            tmpl = get_template('fysm/update_email.txt')
            ctx = Context({
                'group': group_obj,
                'fysm': fysm_obj,
                'view_uri': view_uri,
                'submitter': request.user,
                'request': request,
                'sender': "ASA FYSM team",
            })
            body = tmpl.render(ctx)
            email = EmailMessage(
                subject='FYSM entry for "%s" updated by "%s"' % (
                    group_obj.name,
                    request.user,
                ),
                body=body,
                from_email='asa-fysm@mit.edu',
                to=[group_obj.officer_email, request.user.email, ],
                bcc=['asa-fysm-submissions@mit.edu', ]
            )
            email.send()
            return HttpResponseRedirect(reverse('fysm-thanks', args=[fysm_obj.pk],)) # Redirect after POST

    else:
        form = FYSMRequestForm(instance=fysm_obj, initial=initial, ) # An unbound form

    context = {
        'group':group_obj,
        'fysm':fysm_obj,
        'form':form,
        'categories':forms.models.FYSMCategory.objects.all(),
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
