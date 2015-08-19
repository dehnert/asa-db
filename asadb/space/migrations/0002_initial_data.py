# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models, migrations
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

# W20: mostly cac-card, but some other things
# Walker: keys and combos
# N52: SEMO
# See also discuss[menelaus asa-db 1320]

room_lock_types = (
    ('W20-454',     'cac-key', ),
    ('W20-401D',    'cac-combo', ),
    #('W20-415A',    'inner', ), # APO's press room --- doesn't even have a door
    ('W20-449',     'inner', ),
    ('W20-451A',    'inner', ),
    ('W20-459',     'inner', ),
    ('W20-463',     'inner', ),
    ('W20-481',     'inner', ),
    ('W20-485/A',   'inner', ),

    # 50-XXX offices: see https://diswww.mit.edu/menelaus/asa-db/4606
    ('50-001',      'cac-combo', ),
    ('50-020',      'cac-key', ),
    ('50-023',      'cac-key', ),
    ('50-024',      'cac-combo', ),
    ('50-028',      'cac-combo', ),
    ('50-301',      'group', ),
    ('50-302',      'cac-combo', ),
    ('50-303',      'cac-key', ),
    ('50-304/A',    'cac-combo', ),
    ('50-306',      'cac-key', ),
    ('50-309',      'cac-key', ),
    ('50-316/A',    'cac-key', ),
    ('50-318',      'cac-key', ),
    ('50-320',      'cac-combo', ),
    #('50-352',     'cac-key', ),      # no current occupant
    ('50-354A',     'cac-key', ),
    ('50-356/A',    'cac-key', ),
    ('50-357',      'cac-key', ),
    ('50-358',      'cac-key', ),
    ('50-360',      'cac-key', ),

    # More 50-XXX offices: see https://diswww.mit.edu/menelaus/asa-db/7662
    ('50-220',      'cac-card', ),  # GSC main office
    ('50-209',      'cac-key', ),   # other GSC entries
    ('50-210',      'cac-key', ),   # other GSC entries
    ('50-221',      'cac-key', ),   # other GSC entries
    ('50-222',      'cac-key', ),   # other GSC entries
    ('50-030/ABCD', 'group', ),     # WMBR main office
    ('50-027',      'cac-key', ),   # other WMBR
    ('50-031A',     'cac-key', ),   # other WMBR
    ('50-036',      'cac-key', ),   # other WMBR
    ('50-038/ABCD', 'cac-key', ),   # other WMBR
    ('50-039',      'cac-key', ),   # other WMBR
    ('50-042/A',    'cac-key', ),   # other WMBR
    ('50-025/A',    'cac-key', ),   # set shop
    ('50-045',      'cac-key', ),   # set shop

    # 50-032: See http://asa.scripts.mit.edu/trac/ticket/96#comment:4.
    # The outer door has a keyhole, but all the groups are also in 50-028 and
    # apparently just use the connecting door. The room was originally listed
    # as 50-030, so that also needs to be fixed.
    ('50-032',      'inner', ),
)

def create_lock_types(apps, db_alias):
    lock_types = [
        dict(
            name="CAC Card Access",
            slug="cac-card",
            description="Office with the standard CAC-maintained card access system.",
            info_addr="asa-exec@mit.edu",
            info_url="",
            db_update="cac-card",
        ),
        dict(
            name="Inner",
            slug="inner",
            description="Office accessed through another office owned by the same group, which therefore do not have a separate lock.",
            info_addr="asa-exec@mit.edu",
            info_url="",
            db_update="none",
        ),
        dict(
            name="CAC Combo Only",
            slug="cac-combo",
            description="Room accessible only with a CAC-administered combination, rather than using IDs. Presidents and Treasurers of organizations with this type of lock can come to the CAC office to request a combo change.",
            info_addr="caclocks@mit.edu",
            info_url="",
            db_update="none",
        ),
        dict(
            name="CAC Key",
            slug="cac-key",
            description="Room accessible with a (physical, CAC-administered) key.",
            info_addr="asa-exec@mit.edu",
            info_url="http://web.mit.edu/asa/resources/office-space-alloc.html#access-keys",
            db_update="none",
        ),
        dict(
            name="Unknown",
            slug="unknown",
            description="Room that the ASA does not (currently) know how to manage the access of. (If you know, please tell us at asa-exec@mit.edu.)",
            info_addr="asa-exec@mit.edu",
            info_url="",
            db_update="none",
        ),
        dict(
            name="SEMO",
            slug="semo",
            description="Room with access administered through SEMO (the Security and Emergency Management Office).",
            info_addr="asa-exec@mit.edu",
            info_url="",
            db_update="none",
        ),
        dict(
            name="Group",
            slug="group",
            description="Room with access administered by the group directly.",
            info_addr="asa-exec@mit.edu",
            info_url="",
            db_update="none",
        ),
    ]

    LockType = apps.get_model('space', 'LockType')
    items = [LockType(**kwargs) for kwargs in lock_types]
    LockType.objects.using(db_alias).bulk_create(items)

def set_lock_types(apps, db_alias):
    spaces = apps.get_model('space', 'Space').objects.using(db_alias)
    lock_types = apps.get_model('space', 'LockType').objects.using(db_alias)

    # Fix 50-032 (see http://asa.scripts.mit.edu/trac/ticket/96#comment:4)
    try:
        W030 = spaces.get(number='50-030')
        W030.number = '50-032'
        W030.save()
    except ObjectDoesNotExist:
        logger.info("Could not find 50-030 for renaming to 50-032")

    # Add lock types
    spaces.filter(number__startswith='50-').update(lock_type=lock_types.get(slug='unknown'))
    spaces.filter(number__startswith='N52-').update(lock_type=lock_types.get(slug='semo'))
    created_rooms = []
    for room, lock_type in room_lock_types:
        logger.info("Setting room=%s's lock_type to %s" % (room, lock_type, ))
        lt_obj = lock_types.get(slug=lock_type)
        room_obj, created = spaces.get_or_create(number=room, defaults=dict(lock_type=lt_obj))
        if created: created_rooms.append(room_obj)
        room_obj.lock_type = lt_obj
        room_obj.save()

    for room_obj in created_rooms:
        logger.info("Created %s while setting lock_type" % (room_obj.number, ))

def create_initial_data(apps, schema_editor):
    logger.info("Creating lock types and spaces")
    db_alias = schema_editor.connection.alias
    create_lock_types(apps, db_alias)
    set_lock_types(apps, db_alias)

class Migration(migrations.Migration):

    dependencies = [
        ('space', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
