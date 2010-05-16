#!/usr/bin/python
import sys
import os

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    sys.path.append(django_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import groups.models

if __name__ == '__main__':
    for line in sys.stdin:
        cat_name = line.strip()
        print "Adding category '%s'" % (cat_name, )
        cat = groups.models.ActivityCategory()
        cat.name = cat_name
        cat.save()
