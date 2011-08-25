# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'invoice'
        db.delete_table('payment_invoice')


    def backwards(self, orm):
        
        # Adding model 'invoice'
        db.create_table('payment_invoice', (
            ('price', self.gf('django.db.models.fields.FloatField')()),
            ('item_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('parent_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('payment', ['invoice'])


    models = {
        
    }

    complete_apps = ['payment']
