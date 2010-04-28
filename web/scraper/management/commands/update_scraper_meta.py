import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from scraper.models import Scraper

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
        help='Short name of the scraper to update'),
    )
    help = 'Update various meta data for a scraper or all scrapers.'
    
    def update_meta(self, scraper):
        """
        Takes a scraper object for manipulating.
        
        Don't forget to save() it
        """
        #Do something here
        pass
    
    def handle(self, **options):
        
        if options['short_name']:
            scraper = Scraper.objects.get(short_name=options['short_name'], published=True)
            self.update_meta(scraper)
        else:
            scrapers = Scraper.objects.filter(published=True)
            for scraper in scrapers:
                self.update_meta(scraper)
            

