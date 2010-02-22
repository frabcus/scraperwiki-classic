# encoding: utf-8
"""
Django management command to collate all the alerts for each user, and pass
them on to django-mailer.
"""

from optparse import make_option
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
import settings

from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment
# from scraper.models import Scraper
from frontend.models import UserProfile, Alerts
from market.models import Solicitation
import datetime

import pprint

if "mailer" in settings.INSTALLED_APPS:
    from mailer import send_mail
else:
    from django.core.mail import send_mail


class Command(BaseCommand):
    """
    Django class for management commands
    """

    option_list = BaseCommand.option_list + (
        make_option('--verbose', dest='verbose', action="store_true",
                    help='Print lots'),
        make_option('--dry-run', dest='dry-run', action="store_true",
                    help="Don't send, or update the users last send date"),
    )
    help = 'Send email alerts for users.'

    def __init__(self):
        self.user = None
        self.all_alert_objects = {}
        self.all_alerts = {}
        self.alert_counter = 0
        self.options = {}
        super(Command, self).__init__()

    def send_alerts(self, all_alerts, user):
        """
        Takes a dict of alert types and alerts, passes them though the email
        templates and then sends the mail.

        If django-mailer is installed it will append the mails to its queue.
        This is prefered, as it deals with sending email in a different
        process and requeues them if there was an error sending them.
        """

        # Because we don't have a request object here we can't use the normal
        # RequestContext in render_to_string, so we build it manually
        template_data = {
            'all_alerts': all_alerts,
            'user': user,
            'site': Site.objects.get(id=settings.SITE_ID),
        }

        email_subject = render_to_string('frontend/email_alerts/subject.txt',
                        template_data)
        email_body = render_to_string('frontend/email_alerts/body.txt',
                        template_data)
        if self.options.get('verbose'):
            print email_body
        user_email = user.user.email
        if not self.options.get('dry-run'):
            send_mail(email_subject,
                        email_body,
                        settings.FEEDBACK_EMAIL,
                        (user_email,))

    def scraper_alerts(self, alert_wanted, applies_to, content_type_id):
        """
        Gathers all alerts for all types of scraper alert.

        Types are:
            * contribute
            * follow
        """
        if applies_to == "contribute":
            roles = ['owner', 'editor']
        elif applies_to == "follow":
            roles = ['follow']

        alert_objects = {
            'models':
                self.user.user.scraper_set.filter(
                    userscraperrole__role__in=roles, deleted=False),
            'alert_type': alert_wanted.name}

        alerts = Alerts.objects.filter(
            message_type=alert_objects['alert_type'],
            datetime__gt=self.user.alerts_last_sent,
            content_type=content_type_id,
            object_id__in=[i.pk for i in alert_objects['models']])\
            .order_by('-datetime')
        self.alert_counter += len(alerts)
        if 'scraper' not in self.all_alerts:
            self.all_alerts['scraper'] = {}
        self.all_alerts['scraper'][alert_wanted.name] = alerts

    def market_alerts(self, alert_wanted, applies_to, content_type_id):
        """
        Gathers all alerts for all types of market place alert.

        Types are:
            * all
            * comments
        """

        all_objects = Solicitation.objects.all()

        if applies_to == "all":
            # Gets all objects creted since the alerts were last sent
            alerts = all_objects.filter(
                created_at__gt=self.user.alerts_last_sent)
        if applies_to == "comments":
            # Gets all comments on solicitation objects owned by the user that
            # have been made since last alert send date.
            all_objects.filter(user_created=self.user.user)
            content_type_id = ContentType.objects.get(name="solicitation").pk
            alerts = Comment.objects.filter(
                content_type=content_type_id,
                object_pk__in=[i.pk for i in all_objects],
                submit_date__gt=self.user.alerts_last_sent)
            self.alert_counter += len(alerts)
        if 'solicitation' not in self.all_alerts:
            self.all_alerts['solicitation'] = {}
        self.all_alerts['solicitation'][alert_wanted.name] = alerts

    def handle(self, **options):
        """
        Compile all the alerts to be sent to a user before calling send_alerts
        on them all.

        There are 3 loops needed here.

        1) Loop over all the users that are due to get an alert
        2) Pull in all the *types* of alert that user wants
        3) Loop over all the types and get each alert that relates to it. This
        will normally look up the alerts in the alert table, but some times we
        just need to loop up the models creation/update time
        4) Append all the alerts to a dict, and pass to send_alerts
        """
        self.options = options

        if self.options.get('verbose'):
            pprinter = pprint.PrettyPrinter(indent=4)

        # Get all the users who are due to receive an alert of any kind
        users = UserProfile.objects.extra(
            where=["""
                ADDTIME(alerts_last_sent,
                SEC_TO_TIME(alert_frequency)) < NOW()
                """])
        users.filter(user__is_active=True)

        # Step 1: Loop over the users
        for user in users:
            if self.options.get('verbose'):
                print "Compiling alerts for %s" % user.user.username
            self.user = user

            # All objects that have alerts outstanding
            self.all_alert_objects = {}

            # For storing all the alerts
            self.all_alerts = {}

            # Count of all alerts
            self.alert_counter = 0

            # Step 2: List of alerts the user wants
            alerts_wanted = user.alert_types.all()

            # Step 3: compile a list of all models the user wants alerts about
            for alert_wanted in alerts_wanted:
                content_type = alert_wanted.content_type.model
                content_type_id = \
                        ContentType.objects.get(name=content_type).pk

                applies_to = alert_wanted.applies_to

                # Add each alert –by model and type– here.
                if content_type == "scraper":
                    self.scraper_alerts(
                        alert_wanted,
                        applies_to,
                        content_type_id)

                if content_type == "solicitation":
                    self.market_alerts(
                        alert_wanted,
                        applies_to,
                        content_type_id)

            if self.options.get('verbose'):
                print pprinter.pprint(self.all_alerts)
                print "found %s alerts" % self.alert_counter

            # Done looping over all_alert_types. Let's work out if there
            # actually were any alerts, and send them
            if self.alert_counter > 0:
                # Send the alerts for this user
                self.send_alerts(self.all_alerts, user)
                # With some luck, all the emails send correctly, or raised
                # an exception.
                # Assuming that is the case, update the last_sent date
                user.alerts_last_sent = datetime.datetime.now()
                if not self.options.get('dry-run'):
                    user.save()
            else:
                if self.options.get('verbose'):
                    print "%s has no alerts" % user.user
