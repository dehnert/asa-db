
from south.db import db
from django.db import models
from groups.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Group'
        db.create_table('groups_group', (
            ('id', orm['groups.Group:id']),
            ('name', orm['groups.Group:name']),
            ('abbreviation', orm['groups.Group:abbreviation']),
            ('description', orm['groups.Group:description']),
            ('activity_category', orm['groups.Group:activity_category']),
            ('website_url', orm['groups.Group:website_url']),
            ('constitution_url', orm['groups.Group:constitution_url']),
            ('meeting_times', orm['groups.Group:meeting_times']),
            ('advisor_name', orm['groups.Group:advisor_name']),
            ('num_undergrads', orm['groups.Group:num_undergrads']),
            ('num_grads', orm['groups.Group:num_grads']),
            ('num_community', orm['groups.Group:num_community']),
            ('num_other', orm['groups.Group:num_other']),
            ('group_email', orm['groups.Group:group_email']),
            ('officer_email', orm['groups.Group:officer_email']),
            ('main_account_id', orm['groups.Group:main_account_id']),
            ('funding_account_id', orm['groups.Group:funding_account_id']),
            ('athena_locker', orm['groups.Group:athena_locker']),
            ('recognition_date', orm['groups.Group:recognition_date']),
            ('update_date', orm['groups.Group:update_date']),
            ('updater', orm['groups.Group:updater']),
        ))
        db.send_create_signal('groups', ['Group'])
        
        # Adding model 'ActivityCategory'
        db.create_table('groups_activitycategory', (
            ('id', orm['groups.ActivityCategory:id']),
            ('name', orm['groups.ActivityCategory:name']),
        ))
        db.send_create_signal('groups', ['ActivityCategory'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Group'
        db.delete_table('groups_group')
        
        # Deleting model 'ActivityCategory'
        db.delete_table('groups_activitycategory')
        
    
    
    models = {
        'groups.activitycategory': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'groups.group': {
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
    
    complete_apps = ['groups']
