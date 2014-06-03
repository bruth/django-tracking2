# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Visitor.user'
        db.alter_column(u'tracking_visitor', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['core.VantageUser']))
        # Adding field 'Pageview.referer'
        db.add_column(u'tracking_pageview', 'referer',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)


    def backwards(self, orm):

        # Changing field 'Visitor.user'
        db.alter_column(u'tracking_visitor', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['auth.User']))
        # Deleting field 'Pageview.referer'
        db.delete_column(u'tracking_pageview', 'referer')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.feature': {
            'Meta': {'object_name': 'Feature'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        u'core.organization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Organization'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'numeraljs_locale': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '50'}),
            'python_currency': ('django.db.models.fields.CharField', [], {'default': "'USD'", 'max_length': '50'}),
            'python_locale': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '50'}),
            'tier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Tier']", 'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "'America/Toronto'", 'max_length': '50'})
        },
        u'core.tier': {
            'Meta': {'object_name': 'Tier'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'days_of_history': ('django.db.models.fields.PositiveIntegerField', [], {'default': '90'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'features': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['core.Feature']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        u'core.vantageuser': {
            'Meta': {'object_name': 'VantageUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'users'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['core.Organization']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'user_type': ('django.db.models.fields.CharField', [], {'default': "'CLASSIC'", 'max_length': '10'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'tracking.pageview': {
            'Meta': {'ordering': "('-view_time',)", 'object_name': 'Pageview'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'referer': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'view_time': ('django.db.models.fields.DateTimeField', [], {}),
            'visitor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pageviews'", 'to': u"orm['tracking.Visitor']"})
        },
        u'tracking.visitor': {
            'Meta': {'ordering': "('-start_time',)", 'object_name': 'Visitor'},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'expiry_age': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'expiry_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ip_address': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'time_on_site': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'visit_history'", 'null': 'True', 'to': u"orm['core.VantageUser']"}),
            'user_agent': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['tracking']