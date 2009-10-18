
from south.db import db
from django.db import models
from scraper.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'ScraperVersion'
        db.create_table('scraper_scraperversion', (
            ('id', orm['scraper.ScraperVersion:id']),
            ('scraper', orm['scraper.ScraperVersion:scraper']),
            ('version', orm['scraper.ScraperVersion:version']),
            ('code', orm['scraper.ScraperVersion:code']),
        ))
        db.send_create_signal('scraper', ['ScraperVersion'])
        
        # Adding model 'ScraperException'
        db.create_table('scraper_scraperexception', (
            ('id', orm['scraper.ScraperException:id']),
            ('scraper_invocation', orm['scraper.ScraperException:scraper_invocation']),
            ('message', orm['scraper.ScraperException:message']),
            ('line_number', orm['scraper.ScraperException:line_number']),
            ('backtrace', orm['scraper.ScraperException:backtrace']),
        ))
        db.send_create_signal('scraper', ['ScraperException'])
        
        # Adding model 'UserScraperRole'
        db.create_table('scraper_userscraperrole', (
            ('id', orm['scraper.UserScraperRole:id']),
            ('user', orm['scraper.UserScraperRole:user']),
            ('scraper', orm['scraper.UserScraperRole:scraper']),
            ('role', orm['scraper.UserScraperRole:role']),
        ))
        db.send_create_signal('scraper', ['UserScraperRole'])
        
        # Adding model 'ScraperInvocation'
        db.create_table('scraper_scraperinvocation', (
            ('id', orm['scraper.ScraperInvocation:id']),
            ('scraper_version', orm['scraper.ScraperInvocation:scraper_version']),
            ('run_at', orm['scraper.ScraperInvocation:run_at']),
            ('duration', orm['scraper.ScraperInvocation:duration']),
            ('log_text', orm['scraper.ScraperInvocation:log_text']),
            ('published', orm['scraper.ScraperInvocation:published']),
            ('status', orm['scraper.ScraperInvocation:status']),
        ))
        db.send_create_signal('scraper', ['ScraperInvocation'])
        
        # Adding model 'Scraper'
        db.create_table('scraper_scraper', (
            ('id', orm['scraper.Scraper:id']),
            ('title', orm['scraper.Scraper:title']),
            ('short_name', orm['scraper.Scraper:short_name']),
            ('description', orm['scraper.Scraper:description']),
            ('license', orm['scraper.Scraper:license']),
            ('created_at', orm['scraper.Scraper:created_at']),
            ('published_version', orm['scraper.Scraper:published_version']),
            ('disabled', orm['scraper.Scraper:disabled']),
            ('deleted', orm['scraper.Scraper:deleted']),
            ('status', orm['scraper.Scraper:status']),
        ))
        db.send_create_signal('scraper', ['Scraper'])
        
        # Adding model 'PageAccess'
        db.create_table('scraper_pageaccess', (
            ('id', orm['scraper.PageAccess:id']),
            ('cached_page', orm['scraper.PageAccess:cached_page']),
            ('scraper_invocation', orm['scraper.PageAccess:scraper_invocation']),
        ))
        db.send_create_signal('scraper', ['PageAccess'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'ScraperVersion'
        db.delete_table('scraper_scraperversion')
        
        # Deleting model 'ScraperException'
        db.delete_table('scraper_scraperexception')
        
        # Deleting model 'UserScraperRole'
        db.delete_table('scraper_userscraperrole')
        
        # Deleting model 'ScraperInvocation'
        db.delete_table('scraper_scraperinvocation')
        
        # Deleting model 'Scraper'
        db.delete_table('scraper_scraper')
        
        # Deleting model 'PageAccess'
        db.delete_table('scraper_pageaccess')
        
    
    
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
            'license': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'published_version': ('django.db.models.fields.IntegerField', [], {}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"})
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
