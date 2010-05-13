#!/usr/bin/python
import sys
import os
import csv

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models
import datetime

def dictize_line(header, line,):
    line_dict = {}
    for key, elem in zip(header, line, ):
        line_dict[key]=elem
    return line_dict

def db_parse_date(string):
    return datetime.datetime.strptime(string, '%d-%b-%y').date()

def convert_to_int(number):
    if number == 'n/a': return None
    if number == '': return None
    if number == 'none': return None
    else: return int(number)

if __name__ == '__main__':
    indb = sys.stdin
    reader = csv.reader(indb, delimiter='$')
    header = reader.next()
    for line in reader:
        d = dictize_line(header, line)
        print d
        g = groups.models.Group()
        g.pk                = d['ASA_STUDENT_GROUP_KEY']
        g.name              = d['STUDENT_GROUP_NAME']
        g.abbreviation      = d['STUDENT_GROUP_ACRONYM']
        g.description       = d['STUDENT_GROUP_DESCRIPTION']
        cat_name = d['GROUP_ACTIVITY_CATEGORY']
        try:
            g.activity_category = groups.models.ActivityCategory.objects.get(name=cat_name)
        except groups.models.ActivityCategory.DoesNotExist:
            pass
        g.website_url       = d['WEBSITE_URL']
        g.constitution_url  = d['CONSTITUTION_WEB_URL']
        g.meeting_times     = d['MEETING_TIMES']
        g.advisor_name      = d['ADVISOR']
        g.num_undergrads    = convert_to_int(d['NUM_OF_UNDERGRADUATE'])
        g.num_grads         = convert_to_int(d['NUM_OF_GRADUATE'])
        g.num_community     = convert_to_int(d['NUM_OF_COMMUNITY'])
        g.num_other         = convert_to_int(d['NUM_OF_OTHERS'])
        g.group_email       = d['STUDENT_GROUP_EMAIL']
        g.officer_email     = d['OFFICER_EMAIL']
        g.main_account_id   = convert_to_int(d['MAIN_ACCOUNT_ID'])
        g.funding_account_id= convert_to_int(d['FUNDING_ACCOUNT_ID'])
        g.athena_locker     = d['ATHENA_LOCKER']
        g.recognition_date  = db_parse_date(d['RECOGNITION_DATE'])
        g.update_date       = db_parse_date(d['UPDATE_DATE'])
        g.updater           = d['UPDATER']
        g.save()
