import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

try:
  import json
except:
  import simplejson as json

import subprocess

from scraper.models import Scraper
from frontend.models import Alerts
import frontend
import settings
import datetime
import time

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
        make_option('--verbose', dest='verbose', action="store_true",
                        help='Print lots'),
    )
    help = 'Run a scraper, or all scrapers.  By default all scrapers that are published are run.'
    
    
    def run_scraper(self, scraper, options):
        guid = scraper.guid
        code = scraper.committed_code()
        runner_path = "%s/Runner.py" % settings.FIREBOX_PATH
        failed = False
        
        start = time.time()
        runner = subprocess.Popen(
            [runner_path, '-g', guid], 
            shell=False, 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        runner.stdin.write(code)
        runner.stdin.close()
        for line in runner.stdout:
            if options.get('verbose'):
                print line
            try:
                message = json.loads(line)
                if message['message_type'] == 'fail' or message['message_type'] == 'exception':
                    failed = True
            except:
                pass
        
        elapsed = (time.time() - start)
        if options.get('verbose'): print elapsed

        if failed:
            alert_type = 'run_fail'
        else:
            alert_type = 'run_success'

        # Update the scrapers meta information                    
        scraper.update_meta()
        scraper.last_run = datetime.datetime.now()
        scraper.save()

        # Log this run event to the history table
        alert = Alerts()
        alert.content_object = scraper
        alert.message_type = alert_type
        alert.message_value = elapsed
        alert.save()

    def handle(self, **options):
        if options['short_name']:
            scrapers = Scraper.objects.get(short_name=options['short_name'], published=True, )
            self.run_scraper(scrapers)
        else:

            #get all scrapers where interval > 0 and require running
            scrapers = Scraper.objects.filter(published=True)
            scrapers = Scraper.objects.filter(run_interval__gt=0)
            scrapers = scrapers.extra(where=["ADDTIME(last_run, SEC_TO_TIME(run_interval)) > NOW()"])
            for scraper in scrapers:
                try:
                    self.run_scraper(scraper, options)
                except Exception, e:
                    print "Error running scraper: " + scraper.title
                    print e

        
            

