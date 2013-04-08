# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.core.management import call_command
from django.db import models


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
    ('50-030',      'cac-combo', ), # guess --- matches 50-028, which seems to be same room
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
)

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        call_command("loaddata", "LockTypes.xml")
        lock_types = orm['space.LockType'].objects
        spaces = orm['space.Space'].objects
        spaces.filter(number__startswith='50-').update(lock_type=lock_types.get(slug='unknown'))
        spaces.filter(number__startswith='N52-').update(lock_type=lock_types.get(slug='semo'))
        for room, lock_type in room_lock_types:
            print "Setting room=%s's lock_type to %s" % (room, lock_type, )
            room_obj = spaces.get(number=room)
            room_obj.lock_type = lock_types.get(slug=lock_type)
            room_obj.save()


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'groups.activitycategory': {
            'Meta': {'object_name': 'ActivityCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'groups.group': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Group'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
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
        'space.locktype': {
            'Meta': {'object_name': 'LockType'},
            'db_update': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '20', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info_addr': ('django.db.models.fields.EmailField', [], {'default': "'asa-exec@mit.edu'", 'max_length': '75'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'space.space': {
            'Meta': {'object_name': 'Space'},
            'asa_owned': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['space.LockType']"}),
            'merged_acl': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'space.spaceaccesslistentry': {
            'Meta': {'object_name': 'SpaceAccessListEntry'},
            'card_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)', 'db_index': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['space.Space']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 6, 24, 3, 50, 27, 691752)', 'db_index': 'True'})
        },
        'space.spaceassignment': {
            'Meta': {'object_name': 'SpaceAssignment'},
            'end': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(9999, 12, 31, 23, 59, 59, 999999)', 'db_index': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locker_num': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['space.Space']"}),
            'start': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'})
        }
    }

    complete_apps = ['space']
