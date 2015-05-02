# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OfficerRole'
        db.create_table('groups_officerrole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('max_count', self.gf('django.db.models.fields.IntegerField')(default=10000)),
        ))
        db.send_create_signal('groups', ['OfficerRole'])

        # Adding model 'OfficeHolder'
        db.create_table('groups_officeholder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.OfficerRole'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['groups.Group'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999))),
        ))
        db.send_create_signal('groups', ['OfficeHolder'])


    def backwards(self, orm):
        
        # Deleting model 'OfficerRole'
        db.delete_table('groups_officerrole')

        # Deleting model 'OfficeHolder'
        db.delete_table('groups_officeholder')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_count': ('django.db.models.fields.IntegerField', [], {'default': '10000'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['groups']
