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


Qsa = Q(group_status__slug__in=('active', 'suspended', ))
functions = {
    'finboard' : {
        'format' : "%(name)s;%(officer_email)s",
        'predicate' : Qsa & Q(group_funding__slug='undergrad', group_class__slug='mit-funded', ),
    },
    'nolist' : {
        'format' : "%(name)s <%(officer_email)s>",
        'predicate' : Qsa & Q(officer_email=""),
    },
    'asa-official' : {
        'format' : '"%(name)s" <%(officer_email)s>',
        'predicate' : Q(group_status__slug='active'),
    },
    'emails-only' : {
        'format' : '%(officer_email)s',
        'predicate' : Qsa,
    },
}

def do_output(mode):
    format = functions[mode]['format']
    predicate = functions[mode]['predicate']
    gs = groups.models.Group.objects.filter(predicate)
    for group in gs:
        print format % {
            'name':group.name,
            'officer_email':group.officer_email,
        }

if __name__ == "__main__":
    do_output(sys.argv[1])
