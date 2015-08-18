# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from django.contrib.auth.hashers import make_password
from django.contrib.auth.management import create_permissions

def create_perms(apps, db_alias):
    apps.models_module = True
    create_permissions(apps, verbosity=0)
    apps.models_module = None

def grant_perms(apps, db_alias):
    new_auth_groups = (
        ('mit-sao', (
          ('groups', 'group', 'view_group_private_info', ),
          ('groups', 'group', 'view_signatories', ),
          ('groups', 'groupnote', 'view_note_office', ),
          ('groups', 'group', 'recognize_nge', ),
        )),
        (u'asa-ebm',
         [(u'forms', u'fysm', u'add_fysm'),
          (u'forms', u'fysm', u'change_fysm'),
          (u'forms', u'fysm', u'delete_fysm'),
          (u'forms', u'fysmcategory', u'add_fysmcategory'),
          (u'forms', u'fysmcategory', u'change_fysmcategory'),
          (u'forms', u'fysmcategory', u'delete_fysmcategory'),
          (u'forms', u'groupmembershipupdate', u'add_groupmembershipupdate'),
          (u'forms', u'groupmembershipupdate', u'change_groupmembershipupdate'),
          (u'forms', u'groupmembershipupdate', u'delete_groupmembershipupdate'),
          (u'forms', u'midway', u'add_midway'),
          (u'forms', u'midway', u'change_midway'),
          (u'forms', u'midway', u'delete_midway'),
          (u'forms', u'midwayassignment', u'add_midwayassignment'),
          (u'forms', u'midwayassignment', u'change_midwayassignment'),
          (u'forms', u'midwayassignment', u'delete_midwayassignment'),
          (u'forms', u'pagepreview', u'add_pagepreview'),
          (u'forms', u'pagepreview', u'change_pagepreview'),
          (u'forms', u'pagepreview', u'delete_pagepreview'),
          (u'forms', u'personmembershipupdate', u'add_personmembershipupdate'),
          (u'forms', u'personmembershipupdate', u'change_personmembershipupdate'),
          (u'forms', u'personmembershipupdate', u'delete_personmembershipupdate'),
          (u'groups', u'activitycategory', u'add_activitycategory'),
          (u'groups', u'activitycategory', u'change_activitycategory'),
          (u'groups', u'activitycategory', u'delete_activitycategory'),
          (u'groups', u'group', u'add_group'),
          (u'groups', u'group', u'admin_group'),
          (u'groups', u'group', u'change_group'),
          (u'groups', u'group', u'delete_group'),
          (u'groups', u'group', u'view_group_private_info'),
          (u'groups', u'group', u'view_signatories'),
          (u'groups', u'group', u'recognize_nge'),
          (u'groups', u'group', u'recognize_group'),
          (u'groups', u'groupclass', u'add_groupclass'),
          (u'groups', u'groupclass', u'change_groupclass'),
          (u'groups', u'groupclass', u'delete_groupclass'),
          (u'groups', u'groupfunding', u'add_groupfunding'),
          (u'groups', u'groupfunding', u'change_groupfunding'),
          (u'groups', u'groupfunding', u'delete_groupfunding'),
          (u'groups', u'groupnote', u'add_groupnote'),
          (u'groups', u'groupnote', u'change_groupnote'),
          (u'groups', u'groupnote', u'delete_groupnote'),
          (u'groups', u'groupnote', u'view_note_all'),
          (u'groups', u'groupnote', u'view_note_group'),
          (u'groups', u'groupnote', u'view_note_office'),
          (u'groups', u'groupstatus', u'add_groupstatus'),
          (u'groups', u'groupstatus', u'change_groupstatus'),
          (u'groups', u'groupstatus', u'delete_groupstatus'),
          (u'groups', u'officeholder', u'add_officeholder'),
          (u'groups', u'officeholder', u'change_officeholder'),
          (u'groups', u'officeholder', u'delete_officeholder'),
          (u'groups', u'officerrole', u'add_officerrole'),
          (u'groups', u'officerrole', u'change_officerrole'),
          (u'groups', u'officerrole', u'delete_officerrole'),
          (u'space', u'space', u'add_space'),
          (u'space', u'space', u'change_space'),
          (u'space', u'space', u'delete_space'),
          (u'space', u'spaceassignment', u'add_spaceassignment'),
          (u'space', u'spaceassignment', u'change_spaceassignment'),
          (u'space', u'spaceassignment', u'delete_spaceassignment'),
          (u'space', u'spaceaccesslistentry', u'add_spaceaccesslistentry'),
          (u'space', u'spaceaccesslistentry', u'change_spaceaccesslistentry'),
          (u'space', u'spaceaccesslistentry', u'delete_spaceaccesslistentry'),
        ]),
        (u'mit', []),
        (u'autocreated', []),
        (u'mit-offices',
         [(u'groups', u'group', u'view_group_private_info'),
          (u'groups', u'group', u'view_signatories'),
          (u'groups', u'groupnote', u'view_note_office')]),
        (u'mit-deskworker', [(u'groups', u'group', u'view_signatories')]),
        (u'system:groupadmin',
         [(u'groups', u'group', u'admin_group'),
          (u'groups', u'group', u'view_group_private_info'),
          (u'groups', u'groupnote', u'view_note_group')
        ]),
    )

    ct_man = apps.get_model('contenttypes', 'ContentType').objects.using(db_alias)
    perm_man = apps.get_model('auth', 'Permission').objects.using(db_alias)
    group_man = apps.get_model('auth', 'Group').objects.using(db_alias)
    for group_name, perms in new_auth_groups:
        group, created = group_man.get_or_create(name=group_name)
        for app_name, model_name, codename in perms:
            ct = ct_man.get(model=model_name, app_label=app_name)
            perm = perm_man.get(
                content_type=ct,
                codename=codename,
            )
            group.permissions.add(perm)
    
def create_users(apps, db_alias):
    user_manager = apps.get_model('auth', 'User').objects.using(db_alias)
    group_manager = apps.get_model('auth', 'Group').objects.using(db_alias)
    users = (
        ('groupadmin@SYSTEM', 'Group', 'Administrator', 'asa-db@mit.edu', ),
        ('importer@SYSTEM', 'Data', 'Importer', 'asa-db@mit.edu', ),
        ('gather-constitutions@SYSTEM', 'Gather', 'Constitutions', 'asa-db@mit.edu', ),
    )
    for user, first, last, email in users:
        unusable_pw = make_password(None)
        sys_user, created = user_manager.get_or_create(username=user, defaults={
            'first_name': first,
            'last_name': last,
            'email':email,
            'password':unusable_pw,
        })

    groupadmin_group = group_manager.get(name='system:groupadmin') # created in grant_perms
    groupadmin_user = user_manager.get(username='groupadmin@SYSTEM') # Created just above
    groupadmin_user.groups.add(groupadmin_group)

def update_auth(apps, db_alias):
    create_perms(apps, db_alias)
    grant_perms(apps, db_alias)
    create_users(apps, db_alias)

def create_officerroles(apps, db_alias):
    officerroles = [
        ('President', 'president', 'The president (which sometimes goes by names like "Chair", "Governor", or "Commander") is ultimately responsible for a group\'s operations.', 2, True, 'groupadmin@SYSTEM', True, ),
        ('Treasurer', 'treasurer', 'The Treasurer is the officer responsible for the group\'s finances.', 2, True, 'groupadmin@SYSTEM', True, ),
        ('Financial signatory', 'financial', 'Financial signatories handle the group\'s financial transactions, including approving RFPs, requesting purchase orders, and viewing transaction history.', 6, False, None, True, ),
        ('Reservation signatory', 'reservation', 'Reservation signatories are responsible for reserving space for the group to use.', 10000, False, None, True, ),
        ('Office access', 'office-access', 'People able to use their IDs to get into the offices of this group.', 10000, False, None, False, ),
        ('Shared Storage Access', 'locker-access', 'People with card access for W20-437 and W20-441 shared storage spaces for groups with locker/shelf space in those rooms.', 6, False, None, False, ),
        ("Group Admin", "group-admin", "Group Admins have access to the ASA Group Database's group management functions. Use this to give access to officers besides the President and Treasurer. (This is unnecessary for President and Treasurer, who receive it through those roles instead.)", 3, True, 'groupadmin@SYSTEM', True, ),
        ('GBM Proxy', 'gbm-proxy', 'Person authorized to vote for the group at ASA GBMs. We will only allow people listed as President, Treasurer, Group Admin, or GBM Proxy to be a voting representative of the group. Contact asa-exec@mit.edu or asa-elect@mit.edu with questions. (Additions are enabled starting shortly before each GBM.)', 0, False, None, True, ),
    ]

    user_man = apps.get_model('auth', 'User').objects.using(db_alias)
    role_man = apps.get_model('groups', 'OfficerRole').objects.using(db_alias)

    for officerrole_tuple in officerroles:
        defaults = {}
        defaults['display_name'], slug, defaults['description'], defaults['max_count'], defaults['require_student'], grant_user, defaults['publicly_visible'] = officerrole_tuple
        if grant_user:
            defaults['grant_user'] = user_man.get(username=grant_user)
        officerrole, created = role_man.get_or_create(slug=slug, defaults=defaults)

def create_group_statuses(apps, db_alias):
    classes = [
        ('Sponsored',   'sponsored',    True,   "Sponsored groups receive support (such as funding or space) from a departmental or similar entity.", ),
        ('MIT-funded',  'mit-funded',   True,   "MIT-funded groups are eligible for funding from the UA or GSC funding boards.", ),
        ('Unfunded',    'unfunded',     True,   "Unfunded groups are ineligible for funding from the UA and GSC funding boards and office space.", ),
        ('Club Sport',  'club-sport',   True,   "Club Sports are recognized and funded through the Club Sports Council.", ),
        ('Dorm/FSILG',  'dfsilg',       False,  "Dorm/FSILGs provide housing for MIT students, with varying degrees of Institute recognition/support.", ),
    ]

    statuses = [
        ('Active',      'active',       True,   "Active groups are fully recognized and operational groups.", ),
        ('Suspended',   'suspended',    True,   "Suspended groups have generally been temporarily semi-derecognized and will be fully derecognized if no further action is taken.", ),
        ('Derecognized','derecognized', False,  "Derecognized groups are no longer extant.", ),
        ('Provisional',     'provisional',  True,   "Deprecated", ),
        ('Non-Group Entity', 'nge',         False,  "Non-group entities are entities like (unrecognized) dorms, subgroups of recognized groups, and the like. Often they have some of the attributes or privileges of groups, but not all of them --- for example, they might have an account or be eligible for the Midway.", ),
        ('Applying',      'applying',       False,  "Group currently in the process of applying, but not yet recognized.", ),
    ]

    funding = [
        ('undergraduate',   'undergrad',    'finboard@mit.edu', 'finboard-groups-only', ),
        ('graduate',        'grad',         'gsc-funding@mit.edu', "gsc-fb-", ),
        ('sports council',  'csc',          'csc-officers@mit.edu', "", ),
    ]

    def get_model(name):
        return apps.get_model('groups', name)
    def bulk_create(model, objs):
        model.objects.using(db_alias).bulk_create(objs)

    model = get_model('GroupClass')
    objs = []
    for name, slug, gets_publicity, desc in classes:
        objs.append(model(name=name, slug=slug, gets_publicity=gets_publicity, description=desc))
    bulk_create(model, objs)

    model = get_model('GroupStatus')
    objs = []
    for name, slug, is_active, desc in statuses:
        objs.append(model(name=name, slug=slug, is_active=is_active, description=desc))
    bulk_create(model, objs)

    model = get_model('GroupFunding')
    objs = []
    for name, slug, contact_email, funding_list in funding:
        objs.append(model(name=name, slug=slug, contact_email=contact_email, funding_list=funding_list, ))
    bulk_create(model, objs)


def create_initial_data(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    update_auth(apps, db_alias)
    create_officerroles(apps, db_alias)
    create_group_statuses(apps, db_alias)

class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
        ('forms', '0001_initial'),
        ('space', '0001_initial'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
