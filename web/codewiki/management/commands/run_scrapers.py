import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail

try:    import json
except: import simplejson as json

import subprocess

from codewiki.models import Code, Scraper, ScraperRunEvent, DomainScrape
import frontend
import settings
import datetime
import time
import threading
import urllib2

import re
import os
import signal
import urlparse



# useful function for polling the UML for its current position (don't know where to keep it)
def GetDispatcherStatus():
    result = [ ]
    now = time.time()
    
    fin = urllib2.urlopen(settings.DISPATCHERURL + '/Status')
    lines = fin.readlines()
    for line in lines:
        if re.match("\s*$", line):
            continue
        # Lines are in the form key1=value1;key2=value2;..... Split on ; and then on = and assemble
        # results dictionary. This makes the code independent of ordering. At the end, calculate
        # the run time.
        #
        data = {}
        for pair in line.strip().split(';') :
            key, value = pair.split ('=')
            data[key] = value
        data['runtime'] = now - float(data['time'])
        result.append(data)
    return result
        
def GetUMLstatuses():
    result = { }
    for umlurl in settings.UMLURLS:
        umlname = "uml0"+umlurl[-2:] # make its name
        try:
            stat = urllib2.urlopen(umlurl + "/Status", timeout=2).read()
            result[umlname] = { "runids":re.findall("runID=(.*)\n", stat) }
        except urllib2.URLError, e:
            result[umlname] = { "error":e.reason }
    
    # fake data
    if not settings.UMLURLS:
        result["uml001"] = { "runids":["zzzz.xxx_1", "zzzz.xxx_2"] }
        result["uml002"] = { "error":"bugger bogner" }

    return result


def is_currently_running(scraper):
    return urllib2.urlopen(settings.DISPATCHERURL + '/Status').read().find(scraper.guid) > 0    


def kill_running_runid(runid):
    response = urllib2.urlopen(settings.DISPATCHERURL + '/Kill?'+runid).read()
    mresponse = re.match("Scraper (\S+) (killed|not killed|not found)", response)
    print response
    
    if not mresponse:  return False
    
    assert mresponse
    assert mresponse.group(1) == runid
    if mresponse.group(2) == 'killed':
        return True
    return False



def runmessageloop(runner, event, approxlenoutputlimit):
    # a partial implementation of editor.js
    exceptionmessage = [ ]
    completiondata = None
    outputmessage = [ ]
    tailmessage = [ ]
    domainscrapes = { }  # domain: [domain, pages, bytes] 
    
    temptailmessage = "\n\n[further output lines suppressed]\n"
    while True:
        line = runner.stdout.readline().strip()
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
                event.run_id = data.get("runID")
                event.output = "%s\nEXECUTIONSTATUS: uml=%s runid=%s\n" % (event.output, data.get("uml"), data.get("runID"))
            elif content == "runcompleted":
                completiondata = data
                tailmessage.append("\nEXECUTIONSTATUS: seconds_elapsed=%s CPU_seconds_used=%s\n" % (data.get("elapsed_seconds"), data.get("CPU_seconds"))) 
            event.save()
            
        elif message_type == "sources":
            event.pages_scraped += 1  # soon to be deprecated 
            
            url = data.get('url')
            netloc = "%s://%s" % urlparse.urlparse(url)[:2]
            if not event.first_url_scraped and url and netloc[-16:] != '.scraperwiki.com' and url[-10:] != 'robots.txt':
                event.first_url_scraped = data.get('url')
            if netloc:
                if netloc not in domainscrapes:
                    domainscrapes[netloc] = DomainScrape(scraper_run_event=event, domain=netloc)
                domainscrapes[netloc].pages_scraped += 1
                domainscrapes[netloc].bytes_scraped += int(data.get('bytes'))
        
        elif message_type == "data":
            event.records_produced += 1
        
        elif message_type == "sqlitecall":
            if data.get('insert'):
                event.records_produced += 1
        
        elif message_type == "exception":   # only one of these ever
            event.exception_message = data.get('exceptiondescription')
            
            for stackentry in data.get("stackdump"):
                sMessage = stackentry.get('file')
                if sMessage:
                    if sMessage == "<string>":
                        sMessage = "\nLine %d: %s" % (stackentry.get('linenumber', -1), stackentry.get('linetext'))
                    if stackentry.get('furtherlinetext'):
                        sMessage += " -- " + stackentry.get('furtherlinetext') 
                    exceptionmessage.append(sMessage)
                if stackentry.get('duplicates') and stackentry.get('duplicates') > 1:
                    exceptionmessage.append("  + %d duplicates" % stackentry.duplicates)
            
            if data.get("blockedurl"):
                exceptionmessage.append("Blocked URL: %s" % data.get("blockedurl"))
            exceptionmessage.append('')
            exceptionmessage.append(data.get('exceptiondescription'))
        
        elif message_type == "console":
            while content:
                outputmessage.append(content[:approxlenoutputlimit])
                content = content[approxlenoutputlimit:]
        else:
            outputmessage.append("Unknown: %s\n" % line)
            
        
        # live update of event output so we can watch it when debugging scraperwiki platform
        if outputmessage and len(event.output) < approxlenoutputlimit:
            while outputmessage:
                event.output = "%s%s" % (event.output, outputmessage.pop(0))
                if len(event.output) >= approxlenoutputlimit:
                    event.output = "%s%s" % (event.output, temptailmessage)
                    break
            event.run_ended = datetime.datetime.now()
            event.save()

    # append last few lines of the output
    if outputmessage:
        #assert len(event.output) >= approxlenoutputlimit
        outputtail = [ outputmessage.pop() ] 
        while outputmessage and len(outputtail) < 5 and sum(map(len, outputtail)) < approxlenoutputlimit:
            outputtail.append(outputmessage.pop())
        outputtail.reverse()
            
        if outputmessage:
            tailmessage.insert(0, "\n    [%d lines, %d characters omitted]\n\n" % (len(outputmessage), sum(map(len, outputmessage))))
        event.output = "%s%s%s" % (event.output[:-len(temptailmessage)], "\n".join(tailmessage), "".join(outputtail))
        

    if exceptionmessage:
        event.output = "%s\n\n*** Exception ***\n\n%s\n" % (event.output, "\n".join(exceptionmessage))
    if not completiondata:
        event.output = "%s\nEXECUTIONSTATUS: [Run was interrupted (possibly by a timeout)]\n" % (event.output)
    
    for domainscrape in domainscrapes.values():
        domainscrape.save()

    return exceptionmessage


    # maybe detect the subject title here
def getemailtext(event):
    message = event.output
    message = re.sub("(?:^|\n)EXECUTIONSTATUS:.*", "", message).strip()
    
    msubject = re.search("(?:^|\n)EMAILSUBJECT:(.*)", message)
    if msubject:
        subject = msubject.group(2)    # snip out the subject
        message = "%s%s" % (message[:msubject.start(0)], message[msubject.end(0):])
    else:
        subject = 'Your ScraperWiki Email - %s' % event.scraper.short_name
    
    return subject, message


# class to manage running one scraper
class ScraperRunner(threading.Thread):
    def __init__(self, scraper, verbose):
        super(ScraperRunner, self).__init__()
        self.scraper = scraper
        self.verbose = verbose 
    
    def run(self):
        # Check for possible race condition
        if self.scraper.next_run() >= datetime.datetime.now(): 
            print "Hold on this scraper isn't overdue!!!! %s" % scraper.short_name
            return
        
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
        event.scraper = self.scraper    # better to pointing directly to a code object
        event.pid = runner.pid          # only applies when this runner is active
        event.run_id = ''               # set by execution status
        event.run_started = datetime.datetime.now()   # reset by execution status
        event.run_ended = event.run_started  # actually used as last_updated
        event.output = ""
        event.save()

        exceptionmessage = runmessageloop(runner, event, settings.APPROXLENOUTPUTLIMIT)
        
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

        # Send email if this is an email scraper
        emailers = self.scraper.emailers()
        if emailers.count() > 0:
            subject, message = getemailtext(event)
            if message:  # no email if blank
                for role in emailers:
                    send_mail(subject=subject, message=message, from_email=settings.EMAIL_FROM, recipient_list=[role.user.email], fail_silently=True)


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

        # limit to the first n scrapers
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
                    if options.get('verbose', False):
                        print "%s is already running" % scraper.short_name
            except Exception, e:
                print "Error running scraper: " + scraper.short_name
                print e
