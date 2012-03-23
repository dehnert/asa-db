#!/usr/bin/python

import csv
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db.models import Q

import groups.models


Qsemiactive = Q(group_status__slug__in=('active', 'suspended', ))
functions = {
    'finboard' : {
        'format' : "%(STUDENT_GROUP_NAME)s;%(OFFICER_EMAIL)s",
        'predicate' : Q(group_funding__slug='undergraduate', group_class__slug='mit-funded', ),
    },
    'nolist' : {
        'format' : "%(STUDENT_GROUP_NAME)s <%(OFFICER_EMAIL)s>",
        'predicate' : ~Q(officer_email=""),
    },
    'asa-official' : {
        'format' : '"%(name)s" <%(officer_email)s>',
        'predicate' : Q(group_status__slug='active'),
    },
    'emails-only' : {
        'format' : '%(OFFICER_EMAIL)s',
        'predicate' : Qsemiactive,
    },
}

def do_output(mode):
    format = functions[mode]['format']
    predicate = functions[mode]['predicate']
    gs = groups.models.Group.objects.filter(Qsemiactive & predicate)
    for group in gs:
        print format % {
            'name':group.name,
            'officer_email':group.officer_email,
        }

if __name__ == "__main__":
    do_output(sys.argv[1])
