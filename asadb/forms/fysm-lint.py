#!/usr/bin/python
import sys
import os
import datetime

from django.template import Context, Template
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage

if __name__ == '__main__':
    cur_file = os.path.abspath(__file__)
    django_dir = os.path.abspath(os.path.join(os.path.dirname(cur_file), '..'))
    django_dir_parent = os.path.abspath(os.path.join(os.path.dirname(cur_file), '../..'))
    sys.path.append(django_dir)
    sys.path.append(django_dir_parent)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import forms.models

LEVEL_HIGH   = 'high'
LEVEL_MEDIUM = 'medium'
LEVEL_LOW    = 'low'

def check_display_name(fysm):
    if fysm.display_name[-5:] == ', MIT':
        return {
            'heading': 'Undesirable MIT ending to display name',
            'body':    'It is rarely if ever desirable to end the display name of a group with ", MIT". You may wish to move it to the beginning, or simply remove it entirely.',
            'level':    LEVEL_MEDIUM,
        }
    if ', ' in fysm.display_name:
        return {
            'heading': 'Potentially undesirable comma in display name',
            'body':    'You have a comma in your display name. Frequently this is to move some common word to the end of the group name. You may wish to move such a common word to the front, or leave it out of your advertising entirely.',
            'level':    LEVEL_LOW,
        }

def check_image_field(fysm, label, image):
    good_ext = ['png', 'jpg', 'jpeg', 'gif', ]
    ext = image.name.rsplit('.')[-1]
    convert_msg = 'You should convert it to a PNG (or possibly GIF, if it is essentially all text; or JPEG, if it is mostly images).'
    if not image.name:
        return {
            'heading': 'No %s provided' % (label, ),
            'body': 'You did not upload a %s. We strongly recommended uploading one, since it can help new students to recognize and understand your group.' % (label, ),
            'level': LEVEL_MEDIUM,
        }
    if ext.lower() in ['tif', 'tiff', ]:
        return {
            'heading': 'Undesirable TIFF file submitted for %s' % (label, ),
            'body':    ('You submitted a TIFF file for your %s. TIFF files are generally large and poorly supported by browsers. ' % (label, )) + convert_msg,
            'level':   LEVEL_HIGH,
        }
    if ext.lower() in ['bmp', ]:
        return {
            'heading': 'Undesirable BMP file submitted for %s' % (label, ),
            'body':    ('You submitted a BMP file for your %s. BMP files are generally extremely large. ' % (label, )) + convert_msg,
            'level':   LEVEL_HIGH,
        }
    if not ext.lower() in good_ext:
        print fysm.display_name, image.name, ext, label,
        return {
            'heading': ('Unusual file extension .%s submitted for %s' % (ext, label, )),
            'body':    ('You submitted a .%s file for your %s. This is not one of the extensions that we see very often, which makes it seem somewhat likely to be a bad idea. ' % (ext, label, )) + convert_msg,
            'level':   LEVEL_MEDIUM,
        }

checks = [
    check_display_name,
    lambda f: check_image_field(f, 'logo', f.logo,),
    lambda f: check_image_field(f, 'slide', f.slide,),
]

def run_checks(obj):
    results = []
    for check in checks:
        result = check(obj)
        if result:
            results.append(result)
    return results

def send_emails(objs, template, sender, bcc_recipient, subject_func, recipient_func, ):
    for obj in objs:
        results = run_checks(obj)
        if len(results)>0:
            subject = subject_func(obj)
            ctx = Context({
                'obj': obj,
                'results': results,
            })
            body = tmpl.render(ctx)
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=sender,
                to=recipient_func(obj),
                bcc=[bcc_recipient,]
            )
            email.send()

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-s", "--sender", dest="sender",
                      help="send messages from EMAIL", metavar="EMAIL")
    parser.add_option("-b", "--bcc-recipient", dest="bcc_recipient",
                      help="BCC messages to EMAIL", metavar="EMAIL")
    parser.add_option("-o", "--override-recipient", dest="override_recipient",
                      help="send to EMAIL instead of group emails", metavar="EMAIL")
    parser.add_option("-y", "--year", dest="year",
                      help="process FYSM entries for YEAR", metavar="YEAR")
    parser.set_defaults(
        sender="asa-fysm@mit.edu",
        bcc_recipient='asa-fysm-submissions@mit.edu',
        override_recipient=None,
        year=datetime.date.today().year,
    )
    (options, args) = parser.parse_args()

    if options.override_recipient:
        recipient_func = lambda fysm: [ options.override_recipient, ]
    else:
        recipient_func = lambda fysm: set([ fysm.contact_email, fysm.group.officer_email, ])
    tmpl = get_template('fysm/lint_email.txt')
    send_emails(
        objs=forms.models.FYSM.objects.filter(year=int(options.year),),
        template=tmpl,
        sender=options.sender,
        bcc_recipient=options.bcc_recipient,
        subject_func=lambda f: "FYSM submission for %s" % (f.display_name, ),
        recipient_func=recipient_func,
    )
