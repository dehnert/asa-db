#!/usr/bin/python

import sys
import os

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    proj_dir = os.path.abspath(os.path.join(django_dir, '..'))
    sys.path.append(django_dir)
    sys.path.append(proj_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db import transaction

import forms.models
import groups.models


@transaction.commit_on_success
def revalidate_confirmations():
    confirmations = forms.models.PersonMembershipUpdate.objects.filter(deleted__isnull=True, valid=forms.models.VALID_UNSET)
    accounts = groups.models.AthenaMoiraAccount
    for confirmation in confirmations:
        try:
            person = accounts.active_accounts.get(username=confirmation.username)
            if person.is_student():
                confirmation.valid = forms.models.VALID_AUTOVALIDATED
            else:
                confirmation.valid = forms.models.VALID_AUTOREJECTED

        except accounts.DoesNotExist:
            print "Could not find %s; rejecting" % (confirmation.username, )
            confirmation.valid = forms.models.VALID_AUTOREJECTED
        confirmation.save()

if __name__ == '__main__':
    revalidate_confirmations()
