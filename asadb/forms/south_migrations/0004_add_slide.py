
from south.db import db
from django.db import models
from forms.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'FYSM.slide'
        db.add_column('forms_fysm', 'slide', orm['forms.fysm:slide'])
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'FYSM.slide'
        db.delete_column('forms_fysm', 'slide')
        
    
    
    models = {
        'forms.fysm': {
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['forms.FYSMCategory']", 'blank': 'True'}),
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
            'blurb': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'forms.fysmview': {
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
        'forms.pagepreview': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
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
    
    complete_apps = ['forms']
