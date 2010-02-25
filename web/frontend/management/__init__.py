"""
This is used to emulate fixtures.

We can't use normal fixtures, as AlertTypes have a forign key to
'content_types', and we have no idea what the pk of the content type is before
its been installed.

This files implements a 'post_syncdb' signal
(http://docs.djangoproject.com/en/dev/ref/signals/#django.db.models.signals.post_syncdb)
that will populate the database with AlertTypes

The need for this horrid hack is described here:

http://djangoadvent.com/1.2/natural-keys/

"""

from django.dispatch import dispatcher
from south.signals import post_migrate
from frontend import models as frontend
from scraper import models as scraper
from market import models as market

def create_alert_types(*args, **kwargs):
    if kwargs['app'] == 'frontend':
        
        # delete all old alert types
        frontend.AlertTypes.objects.all().delete()
        
        # Scraper alerts:
        content_pk = scraper.Scraper().content_type()

        alert_types = (
            {
                "name": "run_fail", 
                "applies_to": "contribute", 
                "label": "When a scraper I contribute to fails",
            },
            {
                "name": "commit", 
                "applies_to": "contribute", 
                "label": "When the code in a scraper I contribute to is changed"
            },
            {
                "name": "run_success", 
                "applies_to": "contribute", 
                "label": "When a scraper I contribute to is run"
            },
        )
        for alert in alert_types:
            try:
                existing = frontend.AlertTypes.objects.get(name=alert['name'])
            except frontend.AlertTypes.DoesNotExist:
                alert_model = frontend.AlertTypes()
                alert_model.content_type = content_pk
                alert_model.name = alert['name']
                alert_model.applies_to = alert['applies_to']
                alert_model.label = alert['label']
                alert_model.save()


        # Market alerts:
        content_pk = market.Solicitation().content_type()

        alert_types = (
            {
                "name": "new_solicitations",
                "applies_to": "all", 
                "label": "When someone requests a new dataset to be scraped",
            },
            {
                "name": "market_comment", 
                "applies_to": "comments", 
                "label": "When someone comments on a data request I've made"
            },
        )
        for alert in alert_types:
            try:
                existing = frontend.AlertTypes.objects.get(name=alert['name'])
            except frontend.AlertTypes.DoesNotExist:
                alert_model = frontend.AlertTypes()
                alert_model.content_type = content_pk
                alert_model.name = alert['name']
                alert_model.applies_to = alert['applies_to']
                alert_model.label = alert['label']
                alert_model.save()

post_migrate.connect(create_alert_types)