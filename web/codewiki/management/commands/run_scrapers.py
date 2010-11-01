import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

try:    import json
except: import simplejson as json

import subprocess

from codewiki.models import Code, Scraper, ScraperRunEvent
from frontend.models import Alerts
import frontend
import settings
import datetime
import time
import threading
import urllib

import re
import os
import signal
import urlparse



# useful function for polling the UML for its current position (don't know where to keep it)
def GetUMLrunningstatus():
    result = [ ]
    now = time.time()
    
    
    fin = urllib.urlopen('http://localhost:9000/Status')
    lines = fin.readlines()
    for line in lines:
        if re.match("\s*$", line):
            continue
        mline = re.match('name=\w+;scraperID=([\w\._]*?);testName=([^;]*?);state=(\w);runID=([\w.]*);time=([\d.]*)\s*$', line)
        assert mline, line
        if mline:
            result.append( {'scraperID':mline.group(1), 'testName':mline.group(2), 
                            'state':mline.group(3), 'runID':mline.group(4), 
                            'runtime':now - float(mline.group(5)) } )
    return result


def is_currently_running(scraper):
    return urllib.urlopen('http://localhost:9000/Status').read().find(scraper.guid) > 0    


def kill_running_runid(runid):
    response = urllib.urlopen('http://localhost:9000/Kill?'+runid).read()
    mresponse = re.match("Scraper (\S+) (killed|not killed|not found)", response)
    print response
    
    if not mresponse:  return False
    
    assert mresponse
    assert mresponse.group(1) == runid
    if mresponse.group(2) == 'killed':
        return True
    return False


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
        event.run_id = '???'   # should allow empty
        event.pid = runner.pid # only applies when this runner is active
        event.run_started = datetime.datetime.now()
        event.run_ended = event.run_started  # actually used as last_updated
        event.output = ""
        event.save()

        # a partial implementation of editor.js
        exceptionmessage = [ ]
        completionmessage = [ ]
        outputmessage = [ ]
        firsturl = ''  # to be a member of event
        domainscrapes = { }  # domain: [domain, pages, bytes] 
        
        while True:
            line = runner.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line)
            except:
                data = { 'message_type':'console', 'content':"JSONERROR: "+line }
            
            message_type = data.get('message_type')
            content = data.get("content")
            
            if message_type == 'executionstatus':
                if content == "startingrun":
                    event.run_id = data.get("runID")  # allocated by the UML
                elif content == "runcompleted":
                    completionmessage.append("Finished:: %s seconds elapsed, %s CPU seconds used" % (data.get("elapsed_seconds"), data.get("CPU_seconds"))) 

            elif message_type == "sources":   # data.url, data.bytes
                event.pages_scraped += 1  # soon to be deprecated 
                netloc = urlparse.urlparse(data.url)[1]
                if not firsturl and netloc != 'api.scraperwiki.com':
                    firsturl = data.url
                if netloc and netloc not in domainscrapes:
                    domainscrapes[netloc] = [netloc, 0, 0]  # should be an object
                domainscrapes[netloc][1] += 1
                domainscrapes[netloc][2] += data.bytes
            
            elif message_type == "data":
                event.records_produced += 1
            
            elif message_type == "exception":   # only one of these ever
                for stackentry in data.get("stackdump"):
                    sMessage = stackentry.get('file')
                    if sMessage:
                        if sMessage == "<string>":
                            sMessage = "Line %d: %s" % (stackentry.get('linenumber', -1), stackentry.get('linetext'))
                        if stackentry.get('furtherlinetext'):
                            sMessage += " -- " + stackentry.get('furtherlinetext') 
                        exceptionmessage.append(sMessage)
                if stackentry.get('duplicates') and stackentry.get('duplicates') > 1:
                    exceptionmessage.append("  + %d duplicates" % stackentry.duplicates)
                
                if data.get("blockedurl"):
                    exceptionmessage.append("Blocked URL: %s" % data.get("blockedurl"))
                exceptionmessage.append(data.get('exceptiondescription'))
            
            elif message_type == "console":
                outputmessage.append(content)
            else:
                outputmessage.append("Unknown: %s\n" % line)
                
            
            # inefficient live update of event output so we can watch it when debugging scraperwiki platform
            if outputmessage:
                event.output = "%s%s" % (event.output, "".join(outputmessage))
                outputmessage = [ ]
                event.run_ended = datetime.datetime.now()
                event.save()

        if exceptionmessage:
            event.output = "%s\n\n*** Exception ***\n\n%s\n" % (event.output, "\n".join(exceptionmessage))
        if completionmessage:
            event.output = "%s\n\n%s" % (event.output, "".join(completionmessage))
        elif not exceptionmessage:
            event.output = "%s\n\nRun was interrupted (possibly by a timeout)\n" % (event.output)
        
        event.run_ended = datetime.datetime.now()
        event.pid = -1  # disable it
        event.save()
        
        elapsed = (time.time() - start)

        # Update the scrapers meta information
        self.scraper.update_meta()
        self.scraper.last_run = datetime.datetime.now()
        if exceptionmessage:
            self.scraper.status = 'sick'
        else:
            self.scraper.status = 'ok'
        self.scraper.save()
                    
        # Log this run event to the history table
        alert = Alerts()

        #alert.content_object = self.scraper.code   # saves it as the wrong type
        alert.content_object = Code.objects.get(pk=self.scraper.pk)  # don't have a way to down-cast the scraper object for this useless unhelpful interface
        
            # this is bad, unnecessary and inconsistent with information in the ScraperRunEvent and the scraper.status
        alert.message_type = (bexception or not bcompleted) and 'run_success' or 'run_fail'
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
