import forms.models
import groups.models
import groups.views
import settings
import util.emails

from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.views.generic import list_detail, ListView, DetailView
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage, mail_admins
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.forms import ValidationError
from django.db import connection
from django.db.models import Q, Count

import csv
import datetime
import StringIO

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

    def clean_display_name(self, ):
        name = self.cleaned_data['display_name']
        if ',' in name:
            raise ValidationError("""In general, commas in a display name are a mistake and will look bad (group names like "Punctuation Society, MIT" should probably be "Punctuation Society"). If you do want a comma, contact asa-fysm@mit.edu and we'll put it in for you.""")
        return name

    def clean_description(self, ):
        description = self.cleaned_data['description']
        length = len(description)
        if length > 400:
            raise ValidationError("Descriptions are capped at 400 characters, and this one is %d characters." % (length, ))
        return description

@login_required
def fysm_manage(request, group, ):
    year = datetime.date.today().year
    group_obj = get_object_or_404(groups.models.Group, pk=group)

    initial = {}
    try:
        fysm_obj = forms.models.FYSM.objects.get(group=group_obj, year=year, )
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
            email = util.emails.email_from_template(
                tmpl='fysm/update_email.txt',
                context = Context({
                    'group': group_obj,
                    'fysm': fysm_obj,
                    'view_uri': view_uri,
                    'submitter': request.user,
                    'request': request,
                    'sender': "ASA FYSM team",
                }),
                subject='FYSM entry for "%s" updated by "%s"' % (
                    group_obj.name,
                    request.user,
                ),
                to=[group_obj.officer_email, request.user.email, ],
                from_email='asa-fysm@mit.edu',
            )
            email.bcc = ['asa-fysm-submissions@mit.edu']
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

#####################
# Membership update #
#####################

membership_update_qs = groups.models.Group.objects.filter(group_status__slug__in=['active', 'suspended', ])

class Form_GroupMembershipUpdate(ModelForm):
    group = ModelChoiceField(queryset=membership_update_qs)

    def __init__(self, *args, **kwargs):
        super(Form_GroupMembershipUpdate, self).__init__(*args, **kwargs)
        self.fields['no_hazing'].required = True

    class Meta:
        model = forms.models.GroupMembershipUpdate
        fields = [
            'group',
            'updater_title',
            'group_email',
            'officer_email',
            'email_preface',
            'no_hazing',
            'no_discrimination',
            'membership_definition',
            'num_undergrads',
            'num_grads',
            'num_alum',
            'num_other_affiliate',
            'num_other',
            'membership_list',
        ]

@login_required
def group_membership_update(request, ):
    year = datetime.date.today().year

    initial = {
    }
    update_obj = forms.models.GroupMembershipUpdate()
    update_obj.update_time  = datetime.datetime.now()
    update_obj.updater_name = request.user.username

    confirm_path = reverse('membership-confirm', )
    confirm_uri = '%s://%s%s' % (request.is_secure() and 'https' or 'http',
         request.get_host(), confirm_path)

    if request.method == 'POST': # If the form has been submitted...
        form = Form_GroupMembershipUpdate(request.POST, request.FILES, instance=update_obj) # A form bound to the POST data

        if form.is_valid(): # All validation rules pass
            request_obj = form.save()
            group_obj = request_obj.group


            # Send email
            tmpl = get_template('membership/anti-hazing.txt')
            ctx = Context({
                'update': request_obj,
                'group': group_obj,
                'submitter': request.user,
            })
            body = tmpl.render(ctx)
            email = EmailMessage(
                subject='Anti-Hazing and Non-Discrimination Acknowledgement for %s' % (
                    group_obj.name,
                ),
                body=body,
                from_email=request.user.email,
                to=[request_obj.group_email, ],
                cc=[request_obj.officer_email, ],
                bcc=['asa-db-outgoing@mit.edu', ],
            )
            email.send()

            # Send email
            tmpl = get_template('membership/submit-confirm-email.txt')
            ctx = Context({
                'update': request_obj,
                'group': group_obj,
                'submitter': request.user,
                'confirm_uri': confirm_uri,
            })
            body = tmpl.render(ctx)
            email = EmailMessage(
                subject='ASA Membership Information for %s' % (
                    group_obj.name,
                ),
                body=body,
                from_email=request.user.email,
                to=[request_obj.officer_email, ],
                bcc=['asa-db-outgoing@mit.edu', ],
            )
            email.send()

            return HttpResponseRedirect(reverse('membership-thanks', )) # Redirect after POST

    else:
        form = Form_GroupMembershipUpdate(initial=initial, ) # An unbound form

    context = {
        'form':form,
        'confirm_uri': confirm_uri,
        'pagename':'groups',
    }
    return render_to_response('membership/update.html', context, context_instance=RequestContext(request), )

class Form_PersonMembershipUpdate(ModelForm):
    groups = ModelMultipleChoiceField(queryset=membership_update_qs)
    class Meta:
        model = forms.models.PersonMembershipUpdate
        fields = [
            'groups',
        ]

@login_required
def person_membership_update(request, ):
    year = datetime.date.today().year

    initial = {
    }
    cycle = forms.models.GroupConfirmationCycle.latest()

    # Initialize/find the PersonMembershipUpdate for this user
    try:
        update_obj = forms.models.PersonMembershipUpdate.objects.get(
            username=request.user.username,
            deleted__isnull=True,
            cycle=cycle,
        )
        selected_groups = update_obj.groups.all()
    except forms.models.PersonMembershipUpdate.DoesNotExist:
        update_obj = forms.models.PersonMembershipUpdate()
        update_obj.update_time  = datetime.datetime.now()
        update_obj.username = request.user.username
        update_obj.cycle = cycle
        selected_groups = []

    # Determine whether the submitter is a student or not
    accounts = groups.models.AthenaMoiraAccount
    try:
        person = accounts.active_accounts.get(username=request.user.username)
        if person.is_student():
            update_obj.valid = forms.models.VALID_AUTOVALIDATED
        else:
            update_obj.valid = forms.models.VALID_AUTOREJECTED
    except accounts.DoesNotExist:
        pass
        update_obj.valid = forms.models.VALID_AUTOREJECTED

    update_obj.save()

    # Find groups that list a role for the user
    office_holders = groups.models.OfficeHolder.current_holders.filter(person=request.user.username)
    role_groups = {}
    for office_holder in office_holders:
        if office_holder.group.pk not in role_groups:
            role_groups[office_holder.group.pk] = (office_holder.group, set())
        role_groups[office_holder.group.pk][1].add(office_holder.role.display_name)

    # Find groups the user searched for
    filterset = groups.views.GroupFilter(request.GET, membership_update_qs)
    filtered_groups = filterset.qs.all()
    show_filtered_groups = ('search' in request.GET)

    message = ""
    message_type = "info"

    # Handle the single group add/remove forms
    # * removing previously confirmed groups
    # * add/remove groups that list the user in a role
    # * add/remove groups the user searched for
    if request.method == 'POST' and 'add-remove' in request.POST:
        group = groups.models.Group.objects.get(id=request.POST['group'])
        if request.POST['action'] == 'remove':
            if group in update_obj.groups.all():
                update_obj.groups.remove(group)
                message = "You have successfully unconfirmed membership in %s." % (group, )
            else:
                message = "Removal failed because you had not confirmed membership in %s." % (group, )
                message_type = "warn"
        elif request.POST['action'] == 'add':
            if group in update_obj.groups.all():
                message = "Membership in %s already confirmed." % (group, )
                message_type = "warn"
            else:
                update_obj.groups.add(group)
                message = "You have successfully confirmed membership in %s." % (group, )
        else:
            message = "Uh, somehow you tried to do something besides adding and removing..."
            message_type = "alert"

    # Handle the big list of groups
    if request.method == 'POST' and 'list' in request.POST:
        form = Form_PersonMembershipUpdate(request.POST, request.FILES, instance=update_obj)
        if form.is_valid():
            request_obj = form.save()
            message = "Update saved"
    else:
        form = Form_PersonMembershipUpdate(initial=initial, instance=update_obj, )

    # Render the page
    context = {
        'role_groups':role_groups,
        'form':form,
        'filter':filterset,
        'show_filtered_groups':show_filtered_groups,
        'filtered_groups':filtered_groups,
        'member_groups':selected_groups,
        'message': message,
        'message_type': message_type,
        'pagename':'groups',
    }
    return render_to_response('membership/confirm.html', context, context_instance=RequestContext(request), )


class View_GroupMembershipList(ListView):
    context_object_name = "group_list"
    template_name = "membership/submitted.html"

    def get_queryset(self):
        group_updates = forms.models.GroupMembershipUpdate.objects.all()
        group_updates = group_updates.filter(
            group__personmembershipupdate__deleted__isnull=True,
            group__personmembershipupdate__valid__gt=0,
        )
        group_updates = group_updates.annotate(num_confirms=Count('group__personmembershipupdate'))
        #print len(list(group_updates))
        #for query in connection.queries: print query
        return group_updates


@permission_required('groups.view_group_private_info')
def group_confirmation_issues(request, ):
    active_groups = groups.models.Group.active_groups
    group_updates = forms.models.GroupMembershipUpdate.objects.all()
    people_confirmations = forms.models.PersonMembershipUpdate.objects.filter(
        deleted__isnull=True,
        valid__gt=0,
    )

    buf = StringIO.StringIO()
    output = csv.writer(buf)
    output.writerow(['group_id', 'group_name', 'issue', 'num_confirm', 'officer_email', ])

    q_present = Q(id__in=group_updates.values('group'))
    missing_groups = active_groups.filter(~q_present)
    #print len(list(group_updates))
    for group in missing_groups:
        num_confirms = len(people_confirmations.filter(groups=group))
        output.writerow([
            group.id,
            group.name,
            'unsubmitted',
            num_confirms,
            group.officer_email,
        ])

    for group_update in group_updates:
        group = group_update.group
        num_confirms = len(people_confirmations.filter(groups=group))
        if num_confirms < 5:
            output.writerow([
                group.id,
                group.name,
                'confirmations',
                num_confirms,
                group.officer_email,
            ])


    return HttpResponse(buf.getvalue(), mimetype='text/plain', )
