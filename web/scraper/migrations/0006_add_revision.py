
from south.db import db
from django.db import models
from scraper.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'scraperData'
        db.create_table('scraper_scraperdata', (
            ('id', orm['scraper.scraperdata:id']),
        ))
        db.send_create_signal('scraper', ['scraperData'])
        
        # Adding field 'Scraper.revision'
        db.add_column('scraper_scraper', 'revision', orm['scraper.scraper:revision'])
        
        # Deleting field 'Scraper.published_version'
        db.delete_column('scraper_scraper', 'published_version')
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'scraperData'
        db.delete_table('scraper_scraperdata')
        
        # Deleting field 'Scraper.revision'
        db.delete_column('scraper_scraper', 'revision')
        
        # Adding field 'Scraper.published_version'
        db.add_column('scraper_scraper', 'published_version', orm['scraper.scraper:published_version'])
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'page_cache.cachedpage': {
            'cached_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'post_data': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'time_to_live': ('django.db.models.fields.IntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'scraper.pageaccess': {
            'cached_page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['page_cache.CachedPage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scraper_invocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.ScraperInvocation']"})
        },
        'scraper.scraper': {
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'revision': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"})
        },
        'scraper.scraperdata': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'scraper.scraperexception': {
            'backtrace': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_number': ('django.db.models.fields.IntegerField', [], {}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'scraper_invocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.ScraperInvocation']"})
        },
        'scraper.scraperinvocation': {
            'duration': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log_text': ('django.db.models.fields.TextField', [], {}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'run_at': ('django.db.models.fields.DateTimeField', [], {}),
            'scraper_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.ScraperVersion']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'scraper.scraperrequest': {
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_link': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'scraper.scraperversion': {
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.Scraper']"}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'scraper.userscraperrole': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['scraper.Scraper']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['scraper']
