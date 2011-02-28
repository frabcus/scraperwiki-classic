from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from codewiki.models import View, Scraper
from codewiki.management.screenshooter import ScreenShooter
from itertools import chain

import logging
logging.basicConfig()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
        make_option('--run_scrapers', dest='run_scrapers', action="store_true",
                        help='Should the Scrapers be run?'),
        make_option('--run_views', dest='run_views', action="store_true",
                        help='Should the Views be run?'),
        make_option('--domain', '-d', dest='domain',
                        help='Domain on which the views are running'),
        make_option('--verbose', dest='verbose', action="store_true",
                        help='Print lots'),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.screenshooter = ScreenShooter()

    def add_screenshots(self, view, sizes, options):
        if options['verbose']:
            print "Adding screenshot of %s" % view.short_name

        for size_name, size_values in sizes.items():
            self.screenshooter.add_shot(url = view.get_screenshot_url(options['domain']), 
                                        filename = view.get_screenshot_filepath(size_name),
                                        size = size_values)

    def handle(self, *args, **options):
        if not options['domain']:
            print "You must provide the domain on which the views are running"
            return

        if options['short_name']:
            views = View.unfiltered.filter(short_name=options['short_name'], published=True)
        elif options['run_views']:
            views = View.unfiltered.filter(published=True).order_by("-id")
        else:
            views = []

        for view in views:
            self.add_screenshots(view, settings.VIEW_SCREENSHOT_SIZES, options)

        if options['short_name']:
            scrapers = Scraper.unfiltered.filter(short_name=options['short_name'], published=True)
        elif options['run_scrapers']:
            scrapers = Scraper.unfiltered.filter(published=True).order_by("-id")
        else:
            scrapers = []

        for scraper in scrapers:
            self.add_screenshots(scraper, settings.SCRAPER_SCREENSHOT_SIZES, options)

        if options['verbose']:
            print "------ Starting Screenshooting ------"

        self.screenshooter.run(options['verbose'])
