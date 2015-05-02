# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'GroupMembershipUpdate.num_community'
        db.delete_column('forms_groupmembershipupdate', 'num_community')

        # Adding field 'GroupMembershipUpdate.num_alum'
        db.add_column('forms_groupmembershipupdate', 'num_alum', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding field 'GroupMembershipUpdate.num_other_affiliate'
        db.add_column('forms_groupmembershipupdate', 'num_other_affiliate', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'GroupMembershipUpdate.num_community'
        db.add_column('forms_groupmembershipupdate', 'num_community', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Deleting field 'GroupMembershipUpdate.num_alum'
        db.delete_column('forms_groupmembershipupdate', 'num_alum')

        # Deleting field 'GroupMembershipUpdate.num_other_affiliate'
        db.delete_column('forms_groupmembershipupdate', 'num_other_affiliate')


    models = {
        'forms.fysm': {
            'Meta': {'object_name': 'FYSM'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['forms.FYSMCategory']", 'symmetrical': 'False', 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'join_preview': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forms.PagePreview']", 'null': 'True'}),
            'join_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'slide': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        'forms.fysmcategory': {
            'Meta': {'ordering': "['name']", 'object_name': 'FYSMCategory'},
            'blurb': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'forms.fysmview': {
            'Meta': {'object_name': 'FYSMView'},
            'fysm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forms.FYSM']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'referer': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'source_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'source_user': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'forms.groupmembershipupdate': {
            'Meta': {'object_name': 'GroupMembershipUpdate'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'group_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'membership_definition': ('django.db.models.fields.TextField', [], {}),
            'membership_list': ('django.db.models.fields.TextField', [], {}),
            'no_hazing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'num_alum': ('django.db.models.fields.IntegerField', [], {}),
            'num_grads': ('django.db.models.fields.IntegerField', [], {}),
            'num_other': ('django.db.models.fields.IntegerField', [], {}),
            'num_other_affiliate': ('django.db.models.fields.IntegerField', [], {}),
            'num_undergrads': ('django.db.models.fields.IntegerField', [], {}),
            'officer_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'updater_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'updater_title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'forms.pagepreview': {
            'Meta': {'object_name': 'PagePreview'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'forms.personmembershipupdate': {
            'Meta': {'object_name': 'PersonMembershipUpdate'},
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['groups.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'groups.activitycategory': {
            'Meta': {'object_name': 'ActivityCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'group_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
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
            'updater': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['forms']
