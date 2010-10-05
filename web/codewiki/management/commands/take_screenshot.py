from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from optparse import make_option
from codewiki.models import View
from codewiki.management.screenshooter import ScreenShooter

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
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
            self.screenshooter.add_shot(url = view.get_screenshot_url(), 
                                        filename = view.get_screenshot_filepath(size),
                                        size = settings.SCREENSHOT_SIZES[size])

    def handle(self, *args, **options):
        if options['short_name']:
            views = View.unfiltered.filter(short_name=options['short_name'], published=True)
        else:
            views = View.unfiltered.filter(published=True)

        for view in views:
            try:
                self.add_screenshots(view, options)
            except Exception, ex:
                print "Error taking screenshot of %s" % view.short_name
                print ex

        self.screenshooter.run()
