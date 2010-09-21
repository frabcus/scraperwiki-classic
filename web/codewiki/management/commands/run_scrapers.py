import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

try:    import json
except: import simplejson as json

import subprocess

from codewiki.models import Scraper, ScraperRunEvent
from frontend.models import Alerts
import frontend
import settings
import datetime
import time
import threading
import urllib

import re


# useful function for polling the UML for its current position (don't know where to keep it)
def GetUMLrunningstatus():
    result = [ ]
    now = time.time()
    
    
    fin = urllib.urlopen('http://localhost:9000/Status')
    lines = fin.readlines()
    for line in lines:
        if re.match("\s*$", line):
            continue
        mline = re.match('name=\w+;scraperID=([\w\._]*?);testName=([\w\._]*?);state=(\w);runID=([\w.]*);time=([\d.]*)\s*$', line)
        assert mline, line
        if mline:
            result.append( {'scraperID':mline.group(1), 'testName':mline.group(2), 
                            'state':mline.group(3), 'runID':mline.group(4), 
                            'runtime':now - float(mline.group(5)) } )
    return result

def is_currently_running(scraper):
    return urllib.urlopen('http://localhost:9000/Status').read().find(scraper.guid) > 0    


# class to manage running one scraper
class ScraperRunner(threading.Thread):
    def __init__(self, scraper, verbose):
        super(ScraperRunner, self).__init__()
        self.scraper = scraper
        self.verbose = verbose 
    
    def run(self):
        guid = self.scraper.guid
        code = self.scraper.saved_code().encode('utf-8')

        runner_path = "%s/runner.py" % settings.FIREBOX_PATH
        failed = False
        
        start = time.time()
        args = [runner_path]
        args.append('--guid=%s' % self.scraper.guid)
        args.append('--language=%s' % self.scraper.language.lower())
        args.append('--name=%s' % self.scraper.short_name)
        
        runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        runner.stdin.write(code)
        runner.stdin.close()
        
        event = ScraperRunEvent()
        event.scraper = self.scraper
        event.run_id = '???'
        event.pid = runner.pid
        event.run_started = datetime.datetime.now()
        event.output = ""
        event.save()

        for line in runner.stdout:
            event.output += line
            if self.verbose:
                print "nnn", line
            try:
                message = json.loads(line)
                if message['message_type'] == 'fail' or message['message_type'] == 'exception':
                    failed = True
            except:
                pass

        event.run_ended = datetime.datetime.now()
        event.save()
        
        elapsed = (time.time() - start)
        if self.verbose: 
            print elapsed

        if failed:
            alert_type = 'run_fail'
        else:
            alert_type = 'run_success'

        # Update the scrapers meta information
        self.scraper.update_meta()
        self.scraper.last_run = datetime.datetime.now()
        self.scraper.save()

        # Log this run event to the history table
        alert = Alerts()
        alert.content_object = self.scraper
        alert.message_type = alert_type
        alert.message_value = elapsed
        alert.event_object = event
        alert.save()



# this is invoked by the crontab with the function
#   python manage.py run_scrapers.

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
        make_option('--verbose', dest='verbose', action="store_true",
                        help='Print lots'),
        make_option('--max-concurrent', '-m', dest='max_concurrent',
                        help='Maximum number of scrapers to schedule'),
    )
    help = 'Run a scraper, or all scrapers.  By default all scrapers that are published are run.'

    def run_scraper(self, scraper, options):
        t = ScraperRunner(scraper, options.get('verbose'))
        t.start()

    def get_overdue_scrapers(self):
        #get all scrapers where interval > 0 and require running
        scrapers = Scraper.objects.filter(published=True).filter(run_interval__gt=0)
        scrapers = scrapers.extra(where=["(DATE_ADD(last_run, INTERVAL run_interval SECOND) < NOW() or last_run is null)"])
        return scrapers
    
    def handle(self, **options):
        if options['short_name']:
            scrapers = Scraper.objects.get(short_name=options['short_name'])
            self.run_scraper(scrapers, options)
            return
        
        scrapers = self.get_overdue_scrapers()

        # limit to the first four scrapers
        if 'max_concurrent' in options:
            try:
                scrapers = scrapers[:int(options['max_concurrent'])]
            except:
                pass

        for scraper in scrapers:
            try:
                if not is_currently_running(scraper):
                    self.run_scraper(scraper, options)
                    import time
                    time.sleep(5)
                else:
                    if 'verbose' in options:
                        print "%s is already running" % scraper.short_name
            except Exception, e:
                print "Error running scraper: " + scraper.short_name
                print e
