#from django.core.urlresolvers import reverse
from django.test import TestCase
import datetime
from django.conf import settings
from codewiki.models.scraper import Scraper, ScraperRunEvent
import codewiki

def select_exceptions_that_have_not_been_notified():
    #qs = ScraperRunEvent.objects.filter(scraper=20627).exclude(exception_message='')
    return []

class TestExceptions(TestCase):
    "Test that we can find exceptions"

    runevents_win = 8
    runevents_fail = 4
    pastdays = 3

    def setUp(self):
        self.vault = codewiki.models.Vault.objects.create(user_id = 1)
        self.scraper1 = Scraper.objects.create(
            title=u"Lucky Scraper 1", vault = self.vault,
        )
        self.scraper2 = Scraper.objects.create(
            title=u"Lucky Scraper 2", vault = self.vault,
        )
        self.runevents = []
        self._fakeruns()
        for i in range(self.pastdays):
            self._fakeruns(datetime.datetime.now()-datetime.timedelta(days = i+12))

    def _fakeruns(self, run_started = datetime.datetime.now()):
        for i in range(self.runevents_win):
            scraper = self.scraper1 if i % 2 == 0 else self.scraper2
            runevent = ScraperRunEvent.objects.create(
                scraper=scraper, pid=-1,
                exception_message='',
                run_started=run_started
            )
            self.runevents.append(runevent)

        for i in range(self.runevents_win):
            scraper = self.scraper1 if i % 2 == 0 else self.scraper2
            runevent = ScraperRunEvent.objects.create(
                scraper=scraper, pid=-1,
                exception_message=u'FakeError: This is a test.',
                run_started=run_started
            )
            self.runevents.append(runevent)

    def test_daily_exception_count(self):
        observed_count = len(select_exceptions_that_have_not_been_notified())
        expected_count = self.runevents_win + self.runevents_fail
        self.assertEqual(observed_count, expected_count)
