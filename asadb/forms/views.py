import collections
import csv
import datetime
import StringIO

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.views.generic import list_detail, ListView, DetailView
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template import Context, Template
from django.template.loader import get_template
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage, mail_admins
from django.forms import FileField
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.forms import ValidationError
from django.db import connection
from django.db.models import Q, Count

import django_filters

import forms.models
import groups.models
import groups.views
import util.emails

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

def select_group(request, url_name_after, url_args=[], pagename='homepage', queryset=None, title="", msg=""):
    if request.method == 'POST': # If the form has been submitted...
        # A form bound to the POST data
        form = SelectGroupForm(request.POST, queryset=queryset, )
        if form.is_valid(): # All validation rules pass
            group = form.cleaned_data['group'].id
            return HttpResponseRedirect(reverse(url_name_after, args=url_args+[group],)) # Redirect after POST
    else:
        form = SelectGroupForm(queryset=queryset, ) # An unbound form

    if not title: title = "Select group"
    context = {
        'form':form,
        'title':title,
        'msg':msg,
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

            view_uri = request.build_absolute_uri(reverse('fysm-view', args=[year, request_obj.pk, ]))

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

@login_required
def group_membership_update_select_group(request, ):
    cycle = forms.models.GroupConfirmationCycle.latest()

    users_groups = groups.models.Group.admin_groups(request.user.username)
    qs = membership_update_qs.filter(pk__in=users_groups)

    return select_group(request=request,
        url_name_after='membership-update-group',
        url_args=[cycle.slug],
        pagename='groups',
        queryset=qs,
        title="Submit membership update for...",
    )

class Form_GroupMembershipUpdate(ModelForm):
    def __init__(self, *args, **kwargs):
        super(Form_GroupMembershipUpdate, self).__init__(*args, **kwargs)
        self.fields['no_hazing'].required = True

    class Meta:
        model = forms.models.GroupMembershipUpdate
        fields = [
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
def group_membership_update(request, cycle_slug, pk, ):
    cycle = get_object_or_404(forms.models.GroupConfirmationCycle, slug=cycle_slug)
    group_obj = get_object_or_404(groups.models.Group, pk=pk)
    if not request.user.has_perm('groups.admin_group', group_obj):
        raise PermissionDenied

    try:
        update_obj = forms.models.GroupMembershipUpdate.objects.get(group=group_obj, cycle=cycle, )
    except forms.models.GroupMembershipUpdate.DoesNotExist:
        update_obj = None

    confirm_uri = request.build_absolute_uri(reverse('membership-confirm'))
    submitted_uri = request.build_absolute_uri(reverse('membership-submitted'))

    if request.method == 'POST':
        form = Form_GroupMembershipUpdate(request.POST, request.FILES, instance=update_obj) # A form bound to the POST data

        if form.is_valid(): # All validation rules pass
            # Update the updater info
            form.instance.group = group_obj
            form.instance.cycle = cycle
            form.instance.update_time  = datetime.datetime.now()
            form.instance.updater_name = request.user.username
            request_obj = form.save()

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
                'submitted_uri': submitted_uri,
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
        form = Form_GroupMembershipUpdate(instance=update_obj)

    context = {
        'form':form,
        'group':group_obj,
        'cycle':cycle,
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

    if update_obj.valid <= forms.models.VALID_UNSET:
        message = "You are not listed as a student. While you're welcome to confirm your membership in groups anyway, you will not count towards the five student member requirement. If you are a student, please contact asa-exec so that we can correct our records."
        message_type = "warn"

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
    form.fields['groups'].widget.attrs['size'] = 20

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
        cycle = forms.models.GroupConfirmationCycle.latest()
        group_updates = forms.models.GroupMembershipUpdate.objects.all()
        group_updates = group_updates.filter(
            cycle=cycle,
            group__personmembershipupdate__cycle=cycle,
            group__personmembershipupdate__deleted__isnull=True,
            group__personmembershipupdate__valid__gt=0,
        )
        group_updates = group_updates.annotate(num_confirms=Count('group__personmembershipupdate'))
        #print len(list(group_updates))
        #for query in connection.queries: print query
        return group_updates


class View_GroupConfirmationCyclesList(ListView):
    context_object_name = "cycle_list"
    template_name = "membership/admin.html"
    model = forms.models.GroupConfirmationCycle

    def get_context_data(self, **kwargs):
        context = super(View_GroupConfirmationCyclesList, self).get_context_data(**kwargs)
        context['pagename'] = 'groups'
        return context


@permission_required('groups.view_group_private_info')
def group_confirmation_issues(request, slug, ):
    account_numbers = ("accounts" in request.GET) and request.GET['accounts'] == "1"

    active_groups = groups.models.Group.active_groups
    group_updates = forms.models.GroupMembershipUpdate.objects.filter(cycle__slug=slug, )
    people_confirmations = forms.models.PersonMembershipUpdate.objects.filter(
        deleted__isnull=True,
        valid__gt=0,
        cycle__slug=slug,
    )

    buf = StringIO.StringIO()
    output = csv.writer(buf)
    fields = ['group_id', 'group_name', 'issue', 'num_confirm', 'officer_email', ]
    if account_numbers: fields.append("main_account")
    output.writerow(fields)

    def output_issue(group, issue, num_confirms):
        fields = [
            group.id,
            group.name,
            issue,
            num_confirms,
            group.officer_email,
        ]
        if account_numbers: fields.append(group.main_account_id)
        output.writerow(fields)

    q_present = Q(id__in=group_updates.values('group'))
    missing_groups = active_groups.filter(~q_present)
    #print len(list(group_updates))
    for group in missing_groups:
        num_confirms = len(people_confirmations.filter(groups=group))
        output_issue(group, 'unsubmitted', num_confirms)

    for group_update in group_updates:
        group = group_update.group
        num_confirms = len(people_confirmations.filter(groups=group))
        problems = []

        if num_confirms < 5:
            problems.append("confirmations")

        num_students = group_update.num_undergrads + group_update.num_grads
        num_other = group_update.num_alum + group_update.num_other_affiliate + group_update.num_other
        if num_students < num_other:
            problems.append("50%")

        for problem in problems:
            output_issue(group, problem, num_confirms)

    return HttpResponse(buf.getvalue(), mimetype='text/csv', )



##########
# Midway #
##########


class View_Midways(ListView):
    context_object_name = "midway_list"
    template_name = "midway/midway_list.html"

    def get_queryset(self):
        midways = forms.models.Midway.objects.order_by('date')
        return midways

    def get_context_data(self, **kwargs):
        context = super(View_Midways, self).get_context_data(**kwargs)
        context['pagename'] = 'midway'
        return context

def midway_map_latest(request, ):
    midways = forms.models.Midway.objects.order_by('-date')[:1]
    if len(midways) == 0:
        raise Http404("No midways found.")
    else:
        url = reverse('midway-map', args=(midways[0].slug, ))
        return HttpResponseRedirect(url)


class MidwayAssignmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name='group__name', lookup_type='icontains', label="Name contains")
    abbreviation = django_filters.CharFilter(name='group__abbreviation', lookup_type='iexact', label="Abbreviation is")
    activity_category = django_filters.ModelChoiceFilter(
        label='Activity category',
        name='group__activity_category',
        queryset=groups.models.ActivityCategory.objects,
    )

    class Meta:
        model = forms.models.MidwayAssignment
        fields = [
            'name',
            'abbreviation',
            'activity_category',
        ]
        order_by = (
            ('group__name', 'Name', ),
            ('group__abbreviation', 'Abbreviation', ),
            ('group__activity_category__name', 'Activity category', ),
            ('location', 'Location', ),
        )


class MidwayMapView(DetailView):
    context_object_name = "midway"
    model = forms.models.Midway
    template_name = 'midway/map.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(MidwayMapView, self).get_context_data(**kwargs)
        
        filterset = MidwayAssignmentFilter(self.request.GET)
        context['assignments'] = filterset.qs
        context['filter'] = filterset
        context['pagename'] = 'midway'

        return context


class MidwayAssignmentsUploadForm(Form):
    def validate_csv_fields(upload_file):
        reader = csv.reader(upload_file)
        row = reader.next()
        for col in ('Group', 'officers', 'Table', ):
            if col not in row:
                raise ValidationError('Please upload a CSV file with (at least) columns "Group", "officers", and "Table". (Missing at least "%s".)' % (col, ))

    assignments = FileField(validators=[validate_csv_fields])

@permission_required('forms.add_midwayassignment')
def midway_assignment_upload(request, slug, ):
    midway = get_object_or_404(forms.models.Midway, slug=slug, )

    uploaded = False
    found = []
    issues = collections.defaultdict(list)

    if request.method == 'POST': # If the form has been submitted...
        form = MidwayAssignmentsUploadForm(request.POST, request.FILES, ) # A form bound to the POST data

        if form.is_valid(): # All validation rules pass
            uploaded = True
            reader = csv.DictReader(request.FILES['assignments'])
            for row in reader:
                group_name = row['Group']
                group_officers = row['officers']
                table = row['Table']
                issue = False
                try:
                    group = groups.models.Group.objects.get(name=group_name)
                    assignment = forms.models.MidwayAssignment(
                        midway=midway,
                        location=table,
                        group=group,
                    )
                    assignment.save()
                    found.append(assignment)
                    status = group.group_status.slug
                    if status != 'active':
                        issue = 'status=%s (added anyway)' % (status, )
                except groups.models.Group.DoesNotExist:
                    issue = 'unknown group (ignored)'
                except groups.models.Group.MultipleObjectsReturned:
                    issue = 'multiple groups found (ignored)'
                if issue:
                    issues[issue].append((group_name, group_officers, table))
            for issue in issues:
                issues[issue] = sorted(issues[issue], key=lambda x: x[0])

    else:
        form = MidwayAssignmentsUploadForm() # An unbound form

    context = {
        'midway':midway,
        'form':form,
        'uploaded': uploaded,
        'found': found,
        'issues': dict(issues),
        'pagename':'midway',
    }
    return render_to_response('midway/upload.html', context, context_instance=RequestContext(request), )
