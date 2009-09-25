
from south.db import db
from django.db import models
from page_cache.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'CachedPage'
        db.create_table('page_cache_cachedpage', (
            ('id', orm['page_cache.CachedPage:id']),
            ('url', orm['page_cache.CachedPage:url']),
            ('method', orm['page_cache.CachedPage:method']),
            ('post_data', orm['page_cache.CachedPage:post_data']),
            ('cached_at', orm['page_cache.CachedPage:cached_at']),
            ('time_to_live', orm['page_cache.CachedPage:time_to_live']),
            ('content', orm['page_cache.CachedPage:content']),
        ))
        db.send_create_signal('page_cache', ['CachedPage'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'CachedPage'
        db.delete_table('page_cache_cachedpage')
        
    
    
    models = {
        'page_cache.cachedpage': {
            'cached_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'post_data': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'time_to_live': ('django.db.models.fields.IntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }
    
    complete_apps = ['page_cache']
