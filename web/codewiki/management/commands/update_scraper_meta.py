import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from codewiki.models import Scraper

# this command looks like a botch.  why isn't this data updated when it's run

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
        scraper.update_meta()
        scraper.save()
    
    def handle(self, **options):
        
        if options['short_name']:
            scraper = Scraper.objects.get(short_name=options['short_name'], published=True)
            self.update_meta(scraper)
        else:
            scrapers = Scraper.objects.filter(published=True)
            for scraper in scrapers:
                self.update_meta(scraper)
            

