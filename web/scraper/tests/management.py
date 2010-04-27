import unittest
import datetime
from scraper.models import Scraper
from scraper.management.commands.run_scrapers import Command

class TestRunScrapers(unittest.TestCase):
    def testMe(self):
        command = Command()
        scrapers = command.get_overdue_scrapers()

        # Unpublished scrapers should not appear in the list
        # of scrapers to be run
        unpublised = Scraper(title='Unpublished',
                             published=False, 
                             last_run=None,
                             run_interval=86400)
        unpublised.save()
        self.assertEqual(0, scrapers.count())

        # Published scrapers that have never been run should
        # appear in the list of scrapers to be run
        never_run = Scraper(title='Never Run',
                            published=True, 
                            last_run=None,
                            run_interval=86400)
        never_run.save()
        self.assertEqual(1, scrapers.count())

        # Scrapers that haven't been run for less than the run interval
        # should not appear in the list of scrapers to be run
        not_overdue = Scraper(title='Not Overdue',
                              published=True, 
                              last_run=datetime.datetime.now(), 
                              run_interval=86400)
        not_overdue.save()
        print scrapers.all()
        self.assertEqual(1, scrapers.count())

        # Scrapers that haven't been run for longer than the run interval
        # should appear in the list of scrapers to be run
        overdue = Scraper(published=True, 
                          last_run=datetime.datetime.now() - datetime.timedelta(7), 
                          run_interval=86400)
        overdue.save()
        self.assertEqual(2, scrapers.count())
