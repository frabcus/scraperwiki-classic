from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from codewiki.models import View, Scraper
from codewiki.management.screenshooter import ScreenShooter
from itertools import chain

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
        make_option('--domain', '-d', dest='domain',
                        help='Domain on which the views are running'),
        make_option('--verbose', dest='verbose', action="store_true",
                        help='Print lots'),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.screenshooter = ScreenShooter()

    def add_screenshots(self, view, options):
        if options['verbose']:
            print "Taking screenshot of %s" % view.short_name

        for size in settings.SCREENSHOT_SIZES.keys():
            self.screenshooter.add_shot(url = view.get_screenshot_url(options['domain']), 
                                        filename = view.get_screenshot_filepath(size),
                                        size = settings.SCREENSHOT_SIZES[size])

    def handle(self, *args, **options):
        if not options['domain']:
            print "You must provide the domain on which the views are running"
            return

        if options['short_name']:
            views = View.unfiltered.filter(short_name=options['short_name'], published=True)
        else:
            views = View.unfiltered.filter(published=True)

        if options['short_name']:
            scrapers = Scraper.unfiltered.filter(short_name=options['short_name'], published=True)
        else:
            scrapers = Scraper.unfiltered.filter(published=True)

        for obj in chain(views, scrapers):
            try:
                self.add_screenshots(obj, options)
            except Exception, ex:
                print "Error taking screenshot of %s" % obj.short_name
                print ex

        self.screenshooter.run()
