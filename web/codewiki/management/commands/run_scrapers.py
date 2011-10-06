import django
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, mail_admins
from django.db.models import F
from django.conf import settings

try:    import json
except: import simplejson as json

import subprocess

from codewiki.models import Code, Scraper, ScraperRunEvent, DomainScrape
from codewiki import runsockettotwister
import frontend 

import datetime
import time
import threading
import urllib2
from urllib import urlencode

import re
import os
import signal
import urlparse



# useful function for polling the UML for its current position (don't know where to keep it)
def GetDispatcherStatus():
    result = [ ]
    now = time.time()
    fin,lines = None, None
    
    try:
        # Make an attempt to handle the possibility that the dispatcher is down.
        fin = urllib2.urlopen(settings.DISPATCHERURL + '/Status')
        lines = fin.readlines()
    except urllib2.URLError, e:
        pass
        return None
    else:
        fin.close()
        
        
    for line in lines:
        if re.match("\s*$", line):
            continue
        mline = re.match('uname=([\w\-_\.]+);scraperID=([\w\._]*?);short_name=([^;]*?);runID=([^;]*?);runtime=([\d\.\-]*)\s*$', line)
        assert mline, line
        if mline:
            result.append( {'uname':mline.group(1), 'scraperID':mline.group(2), 'short_name':mline.group(3), 'runID':mline.group(4), 'runtime':float(mline.group(5)) } )
    result.sort(key=lambda x:x["uname"])
    return result


def GetUMLstatuses():
    result = { }
    for umlurl in settings.UMLURLS:
        umlname = "uml0"+umlurl[-2:] # make its name
        try:
            stat, ereason = urllib2.urlopen(umlurl + "/Status", timeout=2).read(), None
        except urllib2.URLError, e:
            stat, ereason = None, e.reason
        except TypeError:
            stat, ereason = urllib2.urlopen(umlurl + "/Status").read(), None  # no timeout field exists in Python2.5
        except:
            stat,ereason = None, 'Bad connection'
            
        if stat:
            result[umlname] = { "runidnames":re.findall("runID=(.*?)&scrapername=(.*)\n", stat) }
        else:
            result[umlname] = { "error":ereason }
            
        
    # fake data
    #if not settings.UMLURLS:
    #    result["uml001"] = { "runids":["zzzz.xxx_1", "zzzz.xxx_2"] }
    #    result["uml002"] = { "error":"bugger bogner" }

    return result


def is_currently_running(scraper):
    return urllib2.urlopen(settings.DISPATCHERURL + '/Status').read().find(scraper.guid) > 0    


def kill_running_runid(runid):
    print settings.DISPATCHERURL + '/Kill?'+runid
    response = urllib2.urlopen(settings.DISPATCHERURL + '/Kill?'+runid).read()
    print response
    mresponse = re.match("Scraper (\S+) (killed|not killed|not found)", response)
    print response
    
    if not mresponse:  
        return False
    
    assert mresponse
    assert mresponse.group(1) == runid
    if mresponse.group(2) == 'killed':
        return True
    return False



def runmessageloop(runnerstream, event, approxlenoutputlimit):
    TAIL_LINES = 5
    # a partial implementation of editor.js
    exceptionmessage = [ ]
    completiondata = None
    outputmessage = [ ]
    domainscrapes = { }  # domain: [domain, pages, bytes] 
    discarded_lines = 0
    discarded_characters = 0
    
    temptailmessage = "\n\n[further output lines suppressed]\n"
    while True:
        line = runnerstream.readline().strip()
        if not line:
            break
        try:
            data = json.loads(line)
        except:
            if len( data.split(':') ) == 2: # Http header?
                continue
            data = { 'message_type':'console', 'content':"JSONERROR: "+line }
        
        message_type = data.get('message_type')
        content = data.get("content")

        if message_type == 'executionstatus':
            if content == "startingrun":
                event.run_id = data.get("runID")
                event.output = "%sEXECUTIONSTATUS: uml=%s runid=%s\n" % (event.output, data.get("uml"), data.get("runID"))
            elif content == "runcompleted":
                completiondata = data
                completionmessage = str(data.get("elapsed_seconds")) + " seconds elapsed, " 
                if data.get("CPU_seconds"):
                    completionmessage += str(data.get("CPU_seconds")) + " CPU seconds used";
                if "exit_status" in data and data.get("exit_status") != 0:
                    completionmessage += ", exit status " + str(data.get("exit_status"));
                if "term_sig_text" in data:
                    completionmessage += ", terminated by " + data.get("term_sig_text");
                elif "term_sig" in data:
                    completionmessage += ", terminated by signal " + str(data.get("term_sig"));
            
            event.save()
            
        elif message_type == "sources":
            event.pages_scraped += 1  
            
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
                        sMessage = "Line %d: %s" % (stackentry.get('linenumber', -1), stackentry.get('linetext'))
                    if stackentry.get('furtherlinetext'):
                        sMessage += " -- " + stackentry.get('furtherlinetext') 
                    exceptionmessage.append(sMessage)
                if stackentry.get('duplicates') and stackentry.get('duplicates') > 1:
                    exceptionmessage.append("  + %d duplicates" % stackentry.get('duplicates'))
            
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

        while len(outputmessage) >= TAIL_LINES:
            discarded = outputmessage.pop(0)
            discarded_lines += 1
            discarded_characters += len(discarded)

    # append last few lines of the output
    if outputmessage:
        #assert len(event.output) >= approxlenoutputlimit
        outputtail = [ outputmessage.pop() ] 
        while outputmessage and len(outputtail) < TAIL_LINES and sum(map(len, outputtail)) < approxlenoutputlimit:
            outputtail.append(outputmessage.pop())
        outputtail.reverse()
            
        omittedmessage = ""
        if discarded_lines > 0:
            omittedmessage = "\n    [%d lines, %d characters omitted]\n\n" % (discarded_lines, discarded_characters)
        event.output = "%s%s%s" % (event.output[:-len(temptailmessage)], omittedmessage, "".join(outputtail))
        

    if exceptionmessage:
        event.output = "%s\n\n*** Exception ***\n\n%s\n" % (event.output, "\n\n".join(exceptionmessage))
    if completiondata:
        event.output = "%s\nEXECUTIONSTATUS: %s\n" % (event.output, completionmessage)
    else:
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
        subject = msubject.group(1)    # snip out the subject
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
            pass # print "\n\nHold on this scraper isn't overdue!!!! %s\n\n" % self.scraper.short_name
            #return
        
        start = time.time()
        
        # this allows for using twister version
        if False:
            qstring = ''
            if self.scraper.privacy_status != 'public':
                # Get all the settings as key=value pairs ready for the query string if protected or 
                # private
                qstring = urlencode(  [ (s.key, s.value,) for s in self.scraper.settings.all() ] )
            runnerstream = runsockettotwister.RunnerSocket()
            runnerstream = runsockettotwister.runscraper(self.scraper, None, qstring)
            pid = os.getpid()
        else:
            guid = self.scraper.guid
            code = self.scraper.saved_code().encode('utf-8')
    
            runner_path = os.path.join(settings.FIREBOX_PATH, "runner.py")
            
            args = [runner_path]
            args.append('--guid=%s' % self.scraper.guid)
            args.append('--language=%s' % self.scraper.language.lower())
            args.append('--name=%s' % self.scraper.short_name)
        
#            if self.scraper.privacy_status != 'public':
#                args.append('--urlquery=%s' % urlencode(  [ (s.key, s.value,) for s in self.scraper.settings.all() ] ) )

            runner = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            runner.stdin.write(code)
            runner.stdin.close()
            runnerstream = runner.stdout
            pid = runner.pid
        
        event = ScraperRunEvent()
        event.scraper = self.scraper    # better to pointing directly to a code object
        event.pid = pid          # only applies when this runner is active
        event.run_id = ''               # set by execution status
        event.run_started = datetime.datetime.now()   # reset by execution status
        event.run_ended = event.run_started  # actually used as last_updated
        event.output = ""
        event.save()

        exceptionmessage = runmessageloop(runnerstream, event, settings.APPROXLENOUTPUTLIMIT)
        
        event.run_ended = datetime.datetime.now()
        event.pid = -1  # disable it
        event.save()
        
        elapsed = (time.time() - start)

        # Update the scrapers meta information. Get the scraper from
        # the db again in case it has changed during the lifetime of the run
        scraper = Scraper.objects.get( id = self.scraper.id )
        scraper.update_meta()
        scraper.last_run = datetime.datetime.now()
        if exceptionmessage:
            scraper.status = 'sick'
        else:
            scraper.status = 'ok'
        scraper.save()

        # Send email if this is an email scraper
        emailers = scraper.users.filter(usercoderole__role='email')
        if emailers.count() > 0:
            subject, message = getemailtext(event)
            if scraper.status == 'ok':
                if message:  # no email if blank
                    for user in emailers:
                        send_mail(subject=subject, message=message, from_email=settings.EMAIL_FROM, recipient_list=[user.email], fail_silently=True)
            else:
                mail_admins(subject="SICK EMAILER: %s" % subject, message=message)


# this is invoked by the crontab with the function
#   python manage.py run_scrapers

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--short_name', '-s', dest='short_name',
                        help='Short name of the scraper to run'),
        make_option('--verbose', dest='verbose', action="store_true",
                        help='Print lots'),
        make_option('--max-concurrent', '-m', dest='max_concurrent',
                        help='Maximum number of scrapers to schedule'),
        make_option('--ignore-emails', dest='ignore_emails', action="store_true",
                        help='Ignore email scrapers'),
                        
    )
    help = 'Run a scraper, or all scrapers.  By default all scrapers are run.'

    def __init__(self):
        self.ignore_emails = False # tests need a default value, so can call get_overdue_scrapers directly
        super(Command, self).__init__

    def run_scraper(self, scraper, options):
        """
        Creates and runs the thread that will actually initiate the execution 
        of the  scraper passed to this method
        """
        t = ScraperRunner(scraper, options.get('verbose'))
        t.start()


    def get_overdue_scrapers(self):
        """
        Obtains a queryset of scrapers that should have already been run, we 
        will order these with the ones that have run least recently hopefully
        being near the top of the list.
        
        If this command was starting with --ignore-emails then we will exclude 
        those scrapers that are actually email scrapers in disguise.
        """
        
        #get all scrapers where interval > 0 and require running
        scrapers = Scraper.objects.exclude(privacy_status="deleted").filter(run_interval__gt=0)
        from django.conf import settings
        scrapers = scrapers.extra(where=[settings.OVERDUE_SQL], params=settings.OVERDUE_SQL_PARAMS).order_by('-last_run')
        
        if self.ignore_emails:
            scrapers = scrapers.exclude(users__usercoderole__role="email")            
        
        return scrapers
    
    
    def handle(self, **options):
        """
        Executes the command by fetching the scrapers that are overdue and 
        sending off messages to the dispatcher to execute them.
        """
        self.ignore_emails = options.get('ignore_emails') or False
                
        if options['short_name']:
            # If given a shortname then just execute that single scraper
            scrapers = Scraper.objects.exclude(privacy_status="deleted").get(short_name=options['short_name'])
            self.run_scraper(scrapers, options)
            return
        
        # Get a list of the scrapers that are overdue
        scrapers = self.get_overdue_scrapers()

        # limit to the first n scrapers if we were told to limit them.
        if 'max_concurrent' in options:
            try:
                scrapers = scrapers[:int(options['max_concurrent'])]
            except:
                pass

        for scraper in scrapers:
            try:
                if not is_currently_running(scraper):
                    self.run_scraper(scraper, options)
                    
                    # Unsure why this is required? Can we safely remove this?
                    import time
                    time.sleep(5)
                else:
                    if options.get('verbose', False):
                        print "%s is already running" % scraper.short_name
            except Exception, e:
                msg = 'There was a problem in run_scrapers:\n%s\n%s' % (scraper.short_name,str(e),)
                mail_admins(subject="[ScraperWiki] run_scrapers error", message=msg, fail_silently=True)                
                
                print "Error running scraper: " + scraper.short_name
                print e
