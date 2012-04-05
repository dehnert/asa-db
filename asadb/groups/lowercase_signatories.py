#!/usr/bin/python
import os
import sys

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.db import transaction
import reversion

import groups.models

@transaction.commit_on_success
def lowercase_signatories():
    with reversion.create_revision():
        for holder in groups.models.OfficeHolder.objects.all():
            if holder.person != holder.person.lower():
                print "Fixing %s" % (holder, )
                holder.person = holder.person.lower()
                holder.save()
        reversion.set_user(None)
        reversion.set_comment("Signatory username lowercasing")

if __name__ == '__main__':
    lowercase_signatories()
