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
from django.contrib.auth.models import User
from south.signals import post_migrate
from frontend import models as frontend
from scraper import models as scraper
from market import models as market

def create_alert_types(*args, **kwargs):
    if kwargs['app'] == 'frontend':        
        existing_pks = []
        # Scraper alerts:
        content_pk = scraper.Scraper().content_type()
        alert_types = [
            {
                "content_pk" : content_pk,
                "name": "run_fail", 
                "applies_to": "contribute", 
                "label": "When a scraper I contribute to fails",
            },
            {
                "content_pk" : content_pk,
                "name": "commit", 
                "applies_to": "contribute", 
                "label": "When the code in a scraper I contribute to is changed"
            },
            {
                "content_pk" : content_pk,
                "name": "run_success", 
                "applies_to": "contribute", 
                "label": "When a scraper I contribute to is run"
            },
            {
                "content_pk" : content_pk,
                "name": "scraper_comment",
                "applies_to": "contribute",
                "label": "New comments on scrapers I contribute to"
            },
        ]

        # Market alerts:
        content_pk = market.Solicitation().content_type()

        alert_types += [
            {
                "content_pk" : content_pk,
                "name": "new_solicitations",
                "applies_to": "all", 
                "label": "When someone requests a new dataset to be scraped",
            },
            {
                "content_pk" : content_pk,
                "name": "market_comment", 
                "applies_to": "comments", 
                "label": "When someone comments on a data request I've made"
            },
        ]
        
        for alert in alert_types:
            try:
                existing = frontend.AlertTypes.objects.get(name=alert['name'])
                existing_pks.append(existing.pk)
            except frontend.AlertTypes.DoesNotExist:
                alert_model = frontend.AlertTypes()
                alert_model.content_type = alert['content_pk']
                alert_model.name = alert['name']
                alert_model.applies_to = alert['applies_to']
                alert_model.label = alert['label']
                alert_model.save()
                existing_pks.append(alert_model.pk)
        
        # Delete all alerts that are not defined here
        for alert in frontend.AlertTypes.objects.all():
            if alert.pk not in existing_pks:
                print "Deleting AlertType: %s" % alert.name
                alert.delete()

post_migrate.connect(create_alert_types)

def add_user_profile_to_super_user(*args, **kwargs):
    """
    The super user created by the syncdb process is
    created before the UserProfile model has been
    migrated.
    """
    if kwargs['app'] == 'frontend':
        for user in User.objects.all():
            if user.userprofile_set.count() == 0:
                frontend.create_user_profile(User, user, True)

post_migrate.connect(add_user_profile_to_super_user)
