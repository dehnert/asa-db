# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

import django.contrib.auth.models

import util.migrations

auth_groups = [
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
]

class Migration(DataMigration):

    depends_on = (
        ("forms", "0001_initial", ),
    )

    def forwards(self, orm):
        "Write your forwards methods here."
        db.send_pending_create_signals()
        util.migrations.migrate_groups_forwards(orm, auth_groups, )
        user_manager = django.contrib.auth.models.User.objects
        groupadmin_user, created = user_manager.get_or_create(username='groupadmin@SYSTEM', defaults={'password':'SYSTEM'})
        groupadmin_group = django.contrib.auth.models.Group.objects.get(name='system:groupadmin')
        groupadmin_user.groups.add(groupadmin_group)


    def backwards(self, orm):
        "Write your backwards methods here."
        print "Warning: not trying to remove groupadmin@SYSTEM user."
        util.migrations.migrate_groups_backwards(orm, auth_groups, )


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'groups.activitycategory': {
            'Meta': {'object_name': 'ActivityCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'groups.athenamoiraaccount': {
            'Meta': {'object_name': 'AthenaMoiraAccount'},
            'account_class': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'add_date': ('django.db.models.fields.DateField', [], {}),
            'del_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'mit_id': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'mod_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mutable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'groups.group': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Group'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'activity_category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.ActivityCategory']", 'null': 'True', 'blank': 'True'}),
            'advisor_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'athena_locker': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'constitution_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'funding_account_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'group_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.GroupClass']"}),
            'group_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'group_funding': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.GroupFunding']", 'null': 'True', 'blank': 'True'}),
            'group_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.GroupStatus']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_account_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'meeting_times': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'num_community': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_grads': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_other': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_undergrads': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'officer_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'recognition_date': ('django.db.models.fields.DateField', [], {}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {}),
            'updater': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'groups.groupclass': {
            'Meta': {'object_name': 'GroupClass'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'gets_publicity': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'groups.groupfunding': {
            'Meta': {'object_name': 'GroupFunding'},
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'funding_list': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'groups.groupnote': {
            'Meta': {'object_name': 'GroupNote'},
            'acl_read_group': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'acl_read_offices': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'groups.groupstartup': {
            'Meta': {'object_name': 'GroupStartup'},
            'create_athena_locker': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'create_group_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'create_officer_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'president_kerberos': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'president_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'stage': ('django.db.models.fields.IntegerField', [], {}),
            'submitter': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'treasurer_kerberos': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'treasurer_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'groups.groupstatus': {
            'Meta': {'object_name': 'GroupStatus'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'groups.officeholder': {
            'Meta': {'object_name': 'OfficeHolder'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.OfficerRole']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'groups.officerrole': {
            'Meta': {'object_name': 'OfficerRole'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'grant_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_count': ('django.db.models.fields.IntegerField', [], {'default': '10000'}),
            'publicly_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'require_student': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['groups']
