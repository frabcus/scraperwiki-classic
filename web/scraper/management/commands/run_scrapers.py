import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

import datetime
import string

import FireStarter
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
        fs  = FireStarter.FireStarter()
        fs.setTestName     ('Runner' )
        fs.setScraperID    (guid)
        # fs.setUser       ('nobody')
        # fs.setGroup       ('nogroup')
        # fs.setTraceback    ('html')
        fs.addPaths        (settings.SMODULES_DIR)
        fs.addPaths        (settings.HOME_DIR+ '/scraperlibs')
        fs.addAllowedSites ('.*\.gov\.uk')
        fs.addAllowedSites ('.*\.org\.uk')
        fs.addAllowedSites ('.*\.co\.uk')
        fs.addAllowedSites ('.*\.com')
        # fs.addIPTables     ('-A OUTPUT -p tcp -d 212.84.75.28 --dport 3306 -j ACCEPT')
        # fs.setEnvironment  ('http_proxy', 'http://192.168.254.101:9002')
        try:
            res = fs.execute (string.replace (code, '\r', ''), False)
            scraper.last_run = datetime.datetime.today()
            scraper.save()
            # Log to history here:
            # print res
        except Exception, e:
            # Log a Firebox fail here
            pass
            
        
        
    def handle(self, **options):
        
        if options['short_name']:
            scrapers = Scraper.objects.get(short_name=options['short_name'], published=True)
            self.run_scraper(scrapers)
        else:
            scrapers = Scraper.objects.filter(published=True)
            for scraper in scrapers:
                self.run_scraper(scraper)
            

    