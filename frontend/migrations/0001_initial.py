
from south.db import db
from django.db import models
from frontend.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'ScraperVersion'
        db.create_table('frontend_scraperversion', (
            ('id', orm['frontend.ScraperVersion:id']),
            ('scraper', orm['frontend.ScraperVersion:scraper']),
            ('version', orm['frontend.ScraperVersion:version']),
            ('code', orm['frontend.ScraperVersion:code']),
        ))
        db.send_create_signal('frontend', ['ScraperVersion'])
        
        # Adding model 'ScraperException'
        db.create_table('frontend_scraperexception', (
            ('id', orm['frontend.ScraperException:id']),
            ('scraper_invocation', orm['frontend.ScraperException:scraper_invocation']),
            ('message', orm['frontend.ScraperException:message']),
            ('line_number', orm['frontend.ScraperException:line_number']),
            ('backtrace', orm['frontend.ScraperException:backtrace']),
        ))
        db.send_create_signal('frontend', ['ScraperException'])
        
        # Adding model 'ScraperInvocation'
        db.create_table('frontend_scraperinvocation', (
            ('id', orm['frontend.ScraperInvocation:id']),
            ('scraper_version', orm['frontend.ScraperInvocation:scraper_version']),
            ('run_at', orm['frontend.ScraperInvocation:run_at']),
            ('duration', orm['frontend.ScraperInvocation:duration']),
            ('log_text', orm['frontend.ScraperInvocation:log_text']),
            ('published', orm['frontend.ScraperInvocation:published']),
            ('status', orm['frontend.ScraperInvocation:status']),
        ))
        db.send_create_signal('frontend', ['ScraperInvocation'])
        
        # Adding model 'UserScraperRole'
        db.create_table('frontend_userscraperrole', (
            ('id', orm['frontend.UserScraperRole:id']),
            ('user_profile', orm['frontend.UserScraperRole:user_profile']),
            ('scraper', orm['frontend.UserScraperRole:scraper']),
            ('role', orm['frontend.UserScraperRole:role']),
        ))
        db.send_create_signal('frontend', ['UserScraperRole'])
        
        # Adding model 'CachedPage'
        db.create_table('frontend_cachedpage', (
            ('id', orm['frontend.CachedPage:id']),
            ('url', orm['frontend.CachedPage:url']),
            ('method', orm['frontend.CachedPage:method']),
            ('post_data', orm['frontend.CachedPage:post_data']),
            ('cached_at', orm['frontend.CachedPage:cached_at']),
            ('time_to_live', orm['frontend.CachedPage:time_to_live']),
            ('content', orm['frontend.CachedPage:content']),
        ))
        db.send_create_signal('frontend', ['CachedPage'])
        
        # Adding model 'Scraper'
        db.create_table('frontend_scraper', (
            ('id', orm['frontend.Scraper:id']),
            ('title', orm['frontend.Scraper:title']),
            ('short_name', orm['frontend.Scraper:short_name']),
            ('description', orm['frontend.Scraper:description']),
            ('license', orm['frontend.Scraper:license']),
            ('created_at', orm['frontend.Scraper:created_at']),
            ('published_version', orm['frontend.Scraper:published_version']),
        ))
        db.send_create_signal('frontend', ['Scraper'])
        
        # Adding model 'Comment'
        db.create_table('frontend_comment', (
            ('id', orm['frontend.Comment:id']),
            ('author', orm['frontend.Comment:author']),
            ('scraper', orm['frontend.Comment:scraper']),
            ('created_at', orm['frontend.Comment:created_at']),
            ('text', orm['frontend.Comment:text']),
        ))
        db.send_create_signal('frontend', ['Comment'])
        
        # Adding model 'UserProfile'
        db.create_table('frontend_userprofile', (
            ('id', orm['frontend.UserProfile:id']),
            ('user', orm['frontend.UserProfile:user']),
            ('email_address', orm['frontend.UserProfile:email_address']),
            ('bio', orm['frontend.UserProfile:bio']),
            ('created_at', orm['frontend.UserProfile:created_at']),
            ('alerts_last_sent', orm['frontend.UserProfile:alerts_last_sent']),
            ('alert_frequency', orm['frontend.UserProfile:alert_frequency']),
        ))
        db.send_create_signal('frontend', ['UserProfile'])
        
        # Adding model 'AlertInstance'
        db.create_table('frontend_alertinstance', (
            ('id', orm['frontend.AlertInstance:id']),
            ('alert_type', orm['frontend.AlertInstance:alert_type']),
            ('user_profile', orm['frontend.AlertInstance:user_profile']),
            ('message', orm['frontend.AlertInstance:message']),
            ('sent', orm['frontend.AlertInstance:sent']),
        ))
        db.send_create_signal('frontend', ['AlertInstance'])
        
        # Adding model 'PageAccess'
        db.create_table('frontend_pageaccess', (
            ('id', orm['frontend.PageAccess:id']),
            ('cached_page', orm['frontend.PageAccess:cached_page']),
            ('scraper_invocation', orm['frontend.PageAccess:scraper_invocation']),
        ))
        db.send_create_signal('frontend', ['PageAccess'])
        
        # Adding model 'AlertNotification'
        db.create_table('frontend_alertnotification', (
            ('id', orm['frontend.AlertNotification:id']),
            ('alert_type', orm['frontend.AlertNotification:alert_type']),
            ('user_profile', orm['frontend.AlertNotification:user_profile']),
        ))
        db.send_create_signal('frontend', ['AlertNotification'])
        
        # Adding model 'UserToUserRole'
        db.create_table('frontend_usertouserrole', (
            ('id', orm['frontend.UserToUserRole:id']),
            ('from_user_profile', orm['frontend.UserToUserRole:from_user_profile']),
            ('to_user_profile', orm['frontend.UserToUserRole:to_user_profile']),
            ('role', orm['frontend.UserToUserRole:role']),
        ))
        db.send_create_signal('frontend', ['UserToUserRole'])
        
        # Adding model 'AlertType'
        db.create_table('frontend_alerttype', (
            ('id', orm['frontend.AlertType:id']),
            ('code', orm['frontend.AlertType:code']),
            ('description', orm['frontend.AlertType:description']),
        ))
        db.send_create_signal('frontend', ['AlertType'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'ScraperVersion'
        db.delete_table('frontend_scraperversion')
        
        # Deleting model 'ScraperException'
        db.delete_table('frontend_scraperexception')
        
        # Deleting model 'ScraperInvocation'
        db.delete_table('frontend_scraperinvocation')
        
        # Deleting model 'UserScraperRole'
        db.delete_table('frontend_userscraperrole')
        
        # Deleting model 'CachedPage'
        db.delete_table('frontend_cachedpage')
        
        # Deleting model 'Scraper'
        db.delete_table('frontend_scraper')
        
        # Deleting model 'Comment'
        db.delete_table('frontend_comment')
        
        # Deleting model 'UserProfile'
        db.delete_table('frontend_userprofile')
        
        # Deleting model 'AlertInstance'
        db.delete_table('frontend_alertinstance')
        
        # Deleting model 'PageAccess'
        db.delete_table('frontend_pageaccess')
        
        # Deleting model 'AlertNotification'
        db.delete_table('frontend_alertnotification')
        
        # Deleting model 'UserToUserRole'
        db.delete_table('frontend_usertouserrole')
        
        # Deleting model 'AlertType'
        db.delete_table('frontend_alerttype')
        
    
    
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
        'frontend.alertinstance': {
            'alert_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.AlertType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'sent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.UserProfile']"})
        },
        'frontend.alertnotification': {
            'alert_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.AlertType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.UserProfile']"})
        },
        'frontend.alerttype': {
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'frontend.cachedpage': {
            'cached_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'post_data': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'time_to_live': ('django.db.models.fields.IntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'frontend.comment': {
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.UserProfile']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.Scraper']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'frontend.pageaccess': {
            'cached_page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.CachedPage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scraper_invocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.ScraperInvocation']"})
        },
        'frontend.scraper': {
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'published_version': ('django.db.models.fields.IntegerField', [], {}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'frontend.scraperexception': {
            'backtrace': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_number': ('django.db.models.fields.IntegerField', [], {}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'scraper_invocation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.ScraperInvocation']"})
        },
        'frontend.scraperinvocation': {
            'duration': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log_text': ('django.db.models.fields.TextField', [], {}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'run_at': ('django.db.models.fields.DateTimeField', [], {}),
            'scraper_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.ScraperVersion']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'frontend.scraperversion': {
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.Scraper']"}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'frontend.userprofile': {
            'alert_frequency': ('django.db.models.fields.IntegerField', [], {}),
            'alerts_last_sent': ('django.db.models.fields.DateTimeField', [], {}),
            'bio': ('django.db.models.fields.TextField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email_address': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'frontend.userscraperrole': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'scraper': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.Scraper']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['frontend.UserProfile']"})
        },
        'frontend.usertouserrole': {
            'from_user_profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_user'", 'to': "orm['frontend.UserProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'to_user_profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_user'", 'to': "orm['frontend.UserProfile']"})
        }
    }
    
    complete_apps = ['frontend']
