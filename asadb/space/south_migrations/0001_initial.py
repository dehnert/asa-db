# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Space'
        db.create_table('space_space', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('asa_owned', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('merged_acl', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('space', ['Space'])

        # Adding model 'SpaceAssignment'
        db.create_table('space_spaceassignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.Group'])),
            ('space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['space.Space'])),
            ('start', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('end', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999))),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('locker_num', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
        ))
        db.send_create_signal('space', ['SpaceAssignment'])

        # Adding model 'SpaceAccessListEntry'
        db.create_table('space_spaceaccesslistentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.Group'])),
            ('space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['space.Space'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 3, 28, 6, 57, 1, 453822))),
            ('end', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999))),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('card_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('space', ['SpaceAccessListEntry'])


    def backwards(self, orm):
        
        # Deleting model 'Space'
        db.delete_table('space_space')

        # Deleting model 'SpaceAssignment'
        db.delete_table('space_spaceassignment')

        # Deleting model 'SpaceAccessListEntry'
        db.delete_table('space_spaceaccesslistentry')


    models = {
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
            'recognition_date': ('django.db.models.fields.DateTimeField', [], {}),
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
        'groups.groupstatus': {
            'Meta': {'object_name': 'GroupStatus'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'space.space': {
            'Meta': {'object_name': 'Space'},
            'asa_owned': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merged_acl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'space.spaceaccesslistentry': {
            'Meta': {'object_name': 'SpaceAccessListEntry'},
            'card_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['space.Space']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 3, 28, 6, 57, 1, 461022)'})
        },
        'space.spaceassignment': {
            'Meta': {'object_name': 'SpaceAssignment'},
            'end': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locker_num': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['space.Space']"}),
            'start': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['space']
