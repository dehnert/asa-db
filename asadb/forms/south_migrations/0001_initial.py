
from south.db import db
from django.db import models
from forms.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'FYSMCategory'
        db.create_table('forms_fysmcategory', (
            ('id', orm['forms.FYSMCategory:id']),
            ('name', orm['forms.FYSMCategory:name']),
            ('slug', orm['forms.FYSMCategory:slug']),
            ('blurb', orm['forms.FYSMCategory:blurb']),
        ))
        db.send_create_signal('forms', ['FYSMCategory'])
        
        # Adding model 'FYSM'
        db.create_table('forms_fysm', (
            ('id', orm['forms.FYSM:id']),
            ('group', orm['forms.FYSM:group']),
            ('display_name', orm['forms.FYSM:display_name']),
            ('year', orm['forms.FYSM:year']),
            ('website', orm['forms.FYSM:website']),
            ('join_url', orm['forms.FYSM:join_url']),
            ('contact_email', orm['forms.FYSM:contact_email']),
            ('description', orm['forms.FYSM:description']),
            ('logo', orm['forms.FYSM:logo']),
            ('tags', orm['forms.FYSM:tags']),
        ))
        db.send_create_signal('forms', ['FYSM'])
        
        # Adding model 'FYSMView'
        db.create_table('forms_fysmview', (
            ('id', orm['forms.FYSMView:id']),
            ('when', orm['forms.FYSMView:when']),
            ('fysm', orm['forms.FYSMView:fysm']),
            ('year', orm['forms.FYSMView:year']),
            ('page', orm['forms.FYSMView:page']),
            ('referer', orm['forms.FYSMView:referer']),
            ('user_agent', orm['forms.FYSMView:user_agent']),
            ('source_ip', orm['forms.FYSMView:source_ip']),
            ('source_user', orm['forms.FYSMView:source_user']),
        ))
        db.send_create_signal('forms', ['FYSMView'])
        
        # Adding ManyToManyField 'FYSM.categories'
        db.create_table('forms_fysm_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('fysm', models.ForeignKey(orm.FYSM, null=False)),
            ('fysmcategory', models.ForeignKey(orm.FYSMCategory, null=False))
        ))
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'FYSMCategory'
        db.delete_table('forms_fysmcategory')
        
        # Deleting model 'FYSM'
        db.delete_table('forms_fysm')
        
        # Deleting model 'FYSMView'
        db.delete_table('forms_fysmview')
        
        # Dropping ManyToManyField 'FYSM.categories'
        db.delete_table('forms_fysm_categories')
        
    
    
    models = {
        'forms.fysm': {
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['forms.FYSMCategory']", 'blank': 'True'}),
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'join_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
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
