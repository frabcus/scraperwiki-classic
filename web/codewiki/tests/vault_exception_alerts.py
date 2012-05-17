import datetime

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from codewiki.models.scraper import Scraper, ScraperRunEvent
from codewiki.models.vault import Vault

def select_exceptions_that_have_not_been_notified():
    # runevents will have a notified flag (not added yet)
    # scrapers that are: in a vault; with an exception; that have not been notified
    # SELECT id from 
    l = []
    for vault in Vault.objects.all():
        for scraper in Scraper.objects.filter(vault=vault):
            runevents = ScraperRunEvent.objects.filter(scraper=scraper)\
                .order_by('-run_started')[:1]
            print runevents
            if not runevents:
                continue
            mostrecent = runevents[0]
            if mostrecent.exception_message:
                l.append(mostrecent)
    return l

class TestExceptions(TestCase):
    "Test that we can find exceptions"

    def setUp(self):
        self.user = User.objects.create_user('dcameron', 'dcameron@scraperwiki.com', 'bagger288')
        self.vault = Vault.objects.create(user = self.user)
        scraper1 = Scraper.objects.create(
            title=u"Lucky Scraper 1", vault = self.vault,
        )
        scraper2 = Scraper.objects.create(
            title=u"Lucky Scraper 2", vault = self.vault,
        )

        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)

        self.runevent1a = ScraperRunEvent.objects.create(
            scraper=scraper1, pid=-1,
            exception_message=u'FakeError: This is a test.',
            run_started=yesterday
        )
        self.runevent1b = ScraperRunEvent.objects.create(
            scraper=scraper1, pid=-1,
            exception_message='',
            run_started=today
        )

        self.runevent2a = ScraperRunEvent.objects.create(
            scraper=scraper2, pid=-1,
            exception_message='',
            run_started=yesterday
        )
        self.runevent2b = ScraperRunEvent.objects.create(
            scraper=scraper2, pid=-1,
            exception_message=u'FakeError: This is a test.',
            run_started=today
        )
        self.runevent2c = ScraperRunEvent.objects.create(
            scraper=scraper2, pid=-1,
            exception_message=u'FakeError: This is a test.',
            run_started=today
        )

    def test_daily_exception_count(self):
        observed_count = len(select_exceptions_that_have_not_been_notified())
        expected_count = 1
        self.assertEqual(observed_count, expected_count)
