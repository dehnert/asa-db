#!/usr/bin/python
import csv
import datetime
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.contrib.auth.models
import reversion

import groups.models

def dictize_line(header, line,):
    line_dict = {}
    for key, elem in zip(header, line, ):
        line_dict[key]=elem
    return line_dict

def canonicalize_email(email):
    if '@' in email: return email
    elif email == '': return ''
    else: return email + "@mit.edu"

def db_parse_date(string):
    return datetime.datetime.strptime(string, '%d-%b-%y').date()

def convert_to_int(number):
    if number == 'n/a': return None
    if number == '': return None
    if number == 'none': return None
    else: return int(number)

def import_group(d):
    g = groups.models.Group()
    g.pk                = d['ASA_STUDENT_GROUP_KEY']
    g.name              = d['STUDENT_GROUP_NAME']
    g.abbreviation      = d['STUDENT_GROUP_ACRONYM']
    g.description       = d['STUDENT_GROUP_DESCRIPTION']
    cat_name = d['GROUP_ACTIVITY_CATEGORY']
    try:
        g.activity_category = groups.models.ActivityCategory.objects.get(name=cat_name)
    except groups.models.ActivityCategory.DoesNotExist:
        print ">> Unknown category '%s' on group '%s'" % (cat_name, g.name, )
        pass
    class_name = d['GROUP_CLASS']
    status_name = d['GROUP_STATUS']
    funding_name = d['GROUP_FUNDING_TYPE']
    if class_name == 'Standard':
        if status_name == 'Provisional':
            class_name = 'Unfunded'
            status_name = 'Active'
        elif status_name == 'Active':
            class_name = 'MIT-funded'
        elif status_name == 'Suspended' or status_name == 'Derecognized':
            class_name = 'MIT-funded'
    g.group_class = groups.models.GroupClass.objects.get(name=class_name)
    g.group_status = groups.models.GroupStatus.objects.get(name=status_name)
    if funding_name == 'none':
        g.group_funding = None
    else:
        g.group_funding = groups.models.GroupFunding.objects.get(name=funding_name)
    g.website_url       = d['WEBSITE_URL']
    g.constitution_url  = d['CONSTITUTION_WEB_URL']
    g.meeting_times     = d['MEETING_TIMES']
    g.advisor_name      = d['ADVISOR']
    g.num_undergrads    = convert_to_int(d['NUM_OF_UNDERGRADUATE'])
    g.num_grads         = convert_to_int(d['NUM_OF_GRADUATE'])
    g.num_community     = convert_to_int(d['NUM_OF_COMMUNITY'])
    g.num_other         = convert_to_int(d['NUM_OF_OTHERS'])
    g.group_email       = canonicalize_email(d['STUDENT_GROUP_EMAIL'])
    g.officer_email     = canonicalize_email(d['OFFICER_EMAIL'])
    try:
        g.main_account_id   = convert_to_int(d['MAIN_ACCOUNT_ID'])
    except ValueError:
        if d['MAIN_ACCOUNT_ID'] == "contact LWard":
            print "Ignoring account ID contact LWard..."
            g.main_account_id = None
        else:
            raise
    g.funding_account_id= convert_to_int(d['FUNDING_ACCOUNT_ID'])
    g.athena_locker     = d['ATHENA_LOCKER']
    g.recognition_date  = db_parse_date(d['RECOGNITION_DATE'])
    g.update_date       = db_parse_date(d['UPDATE_DATE'])
    g.updater           = d['UPDATER']
    g.save()

if __name__ == '__main__':
    indb = sys.stdin
    reader = csv.reader(indb)
    header = reader.next()
    with reversion.create_revision():
        for line in reader:
            d = dictize_line(header, line)
            print d
            import_group(d)
        importer = django.contrib.auth.models.User.objects.get(username='importer@SYSTEM', )
        reversion.set_user(importer)
        reversion.set_comment("Groups importer")
