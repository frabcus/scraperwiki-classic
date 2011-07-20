from django.conf      import settings
from django.core.mail import send_mail, mail_admins
from codewiki.models  import Code, Scraper, ScraperRunEvent, DomainScrape
from codewiki         import runsockettotwister

import frontend 
import os, sys
import ConfigParser
import Queue
import datetime, time,random, threading

try:    import json
except: import simplejson as json

from runner import Runner, execute_runner
import logging
import logging


def runmessageloop(runnerstream, event, approxlenoutputlimit):
    """
    Acts as the intermediary in passing output from the script to the 
    twister instance so it can be sent back to the client.
    """
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


def run_scraper(scraper, config_dict):
    """
    Responsible for creating the runner object for the scraper and 
    handling the message loop until it is complete.
    """
    try:
        code = scraper.saved_code().encode('utf-8')
    except:
        code = 'print 1 + 2'

    options = {
        'guid'      : scraper.guid,
        'language'  : scraper.language.lower(),
        'name'      : scraper.short_name,
        'cpulimit'  : 80,
        'urlquery'  : '',
        'draft'     : False,
    }
    
    pid = os.getpid()
        
    start = time.time()    
        
    runner = Runner(code, config_dict)
    jdata = runner.build_run_data( options )
    
    thread = threading.Thread(target=execute_runner, args=(config_dict['dhost'], config_dict['dport'], jdata,) )
    thread.start()
    
    event = ScraperRunEvent()
    event.scraper = scraper    # better to pointing directly to a code object
    event.pid     = pid        # only applies when this runner is active
    event.run_id  = ""         # set by execution status
    event.output  = ""    
    event.run_started = datetime.datetime.now()   # reset by execution status
    event.run_ended   = event.run_started  # actually used as last_updated
    event.save()

    exceptionmessage = ''
    try:
        exceptionmessage = runmessageloop(sys.stdout, event, settings.APPROXLENOUTPUTLIMIT)
    except IOError, e:
        pass
    
    while thread and thread.isAlive():
        thread.join()

    event.run_ended = datetime.datetime.now()
    event.pid = -1  # disable it
    event.save()
    
    elapsed = (time.time() - start)

    # Update the scrapers meta information. Get the scraper from
    # the db again in case it has changed during the lifetime of the run
    scraper = Scraper.objects.get( id = scraper.id )
    try:
        scraper.update_meta()
    except:
        # Might fail if we can't get to the data proxy
        pass
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


def subprocessor(queue, config_dict):
    """
    This is the main method for the newly multi-process spawned worker
    that will keep trying to get work off the queue and then run it.
    """
    pid = os.getpid()
    name = '%s_%s' % (__name__,pid,)
    
    while True:
        logging.debug( '%s is waiting' % name )
        job = queue.get()
        
        if job['task'] == 'run':
            scraper = Scraper.objects.get( pk=job['scraper'] )
            
            logging.debug( '(%s) got %s' % (name, scraper,) )
            run_scraper( scraper, config_dict)
