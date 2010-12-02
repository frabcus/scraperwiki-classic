import unittest
import datetime
from codewiki.models import Scraper
from codewiki.management.commands.run_scrapers import Command

class TestRunScrapers(unittest.TestCase):
    def setUp(self):
        # Remove any Scrapers created by a fixture
        [x.delete() for x in Scraper.objects.all()]
        command = Command()
        self.scrapers = command.get_overdue_scrapers()

    def testUnpublished(self):
        # Unpublished scrapers should not appear in the list
        # of scrapers to be run
        unpublished = Scraper(title='Unpublished',
                             published=False, 
                             last_run=None,
                             run_interval=86400)
        unpublished.buildfromfirsttitle()
        unpublished.save()
        self.assertEqual(0, self.scrapers.count())

    def testNeverRun(self):
        # Published scrapers that have never been run should
        # appear in the list of scrapers to be run
        never_run = Scraper(title='Never Run',
                            published=True, 
                            last_run=None,
                            run_interval=86400)
        never_run.buildfromfirsttitle()
        never_run.save()
        self.assertEqual(1, self.scrapers.count())

    def testNotOverdue(self):
        # Scrapers that haven't been run for less than the run interval
        # should not appear in the list of scrapers to be run
        not_overdue = Scraper(title='Not Overdue',
                              published=True, 
                              last_run=datetime.datetime.now(), 
                              run_interval=86400)
        not_overdue.buildfromfirsttitle()
        not_overdue.save()
        self.assertEqual(0, self.scrapers.count())

    def testOverdue(self):
        # Scrapers that haven't been run for longer than the run interval
        # should appear in the list of scrapers to be run
        overdue = Scraper(published=True, 
                          last_run=datetime.datetime.now() - datetime.timedelta(7), 
                          run_interval=86400)
        overdue.buildfromfirsttitle()
        overdue.save()
        self.assertEqual(1, self.scrapers.count())
