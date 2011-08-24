# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'alerttype'
        db.delete_table('notification_alerttype')

        # Deleting model 'alertnotification'
        db.delete_table('notification_alertnotification')

        # Deleting model 'alertinstance'
        db.delete_table('notification_alertinstance')


    def backwards(self, orm):
        
        # Adding model 'alerttype'
        db.create_table('notification_alerttype', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('notification', ['alerttype'])

        # Adding model 'alertnotification'
        db.create_table('notification_alertnotification', (
            ('alert_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['notification.AlertType'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('notification', ['alertnotification'])

        # Adding model 'alertinstance'
        db.create_table('notification_alertinstance', (
            ('alert_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['notification.AlertType'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sent', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('notification', ['alertinstance'])


    models = {
        
    }

    complete_apps = ['notification']
