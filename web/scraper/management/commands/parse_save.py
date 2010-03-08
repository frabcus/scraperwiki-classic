import re

import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from scraper.models import Scraper

class Command(BaseCommand):
    def __init__(self):
        self.path = '/tmp/save_calls/'
    
    
    def parse_scraper(self, scraper):
        code = scraper.committed_code()
        save_calls = re.findall('(save\(.*)', code)
        if save_calls:
            scraper_file = open(self.path+scraper.guid, 'w')
            scraper_file.write("\n".join(save_calls))
            
    
    def handle(self, **options):    
        scrapers = Scraper.objects.all()
        for scraper in scrapers:
            self.parse_scraper(scraper)
            

