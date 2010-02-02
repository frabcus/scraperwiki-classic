import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

import json
import subprocess

from scraper.models import Scraper
import settings


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
        help='Short name of the scraper to run'),
    )
    help = 'Run a scraper, or all scrapers.  By default all scrapers that are published are run.'
    
    
    def run_scraper(self, scraper):
        guid = scraper.guid
        code = scraper.committed_code()
        runner_path = "%s/Runner.py" % settings.FIREBOX_PATH
        runner = subprocess.Popen([runner_path, '-g', guid], shell=False, stdin=subprocess.PIPE)
        runner.communicate(code)
        
        
    def handle(self, **options):
        if options['short_name']:
            scrapers = Scraper.objects.get(short_name=options['short_name'], published=True, )
            self.run_scraper(scrapers)
        else:
            scrapers = Scraper.objects.exclude(run_interval='never').filter(published=True)
            for scraper in scrapers:
                self.run_scraper(scraper)


        
            

