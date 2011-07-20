import sys
sys.path.append('/var/www/scraperwiki/web')

from django.conf      import settings
from django.core.mail import send_mail, mail_admins
from codewiki.models  import Code, Scraper, ScraperRunEvent, DomainScrape
from codewiki         import runsockettotwister

import frontend 
import os, time
import ConfigParser

try:    import json
except: import simplejson as json

from worker import subprocessor
from multiprocessing import Process, Queue
from multiprocesslogger import MultiProcessingLog
    
import logging
    
class Scheduler(object):
    """
    The Scheduler service is responsible for keeping a steady stream of scrapers
    being passed through to the relevant processor for execution.  As a long 
    running process this app will be responsible for creating processes that will
    monitor a queue (when not working) for more scrapers to run and then run them.

    Each of the spawned multi-processes will incorporate the code from the old
    runner.py file so that it is handled in the same way as previously - for now.
    """
    
    def is_currently_running(self, scraper):
        """
        Returns True if the dispatcher thinks that the scraper is currently running
        """
        try:
            return urllib2.urlopen(settings.DISPATCHERURL + '/Status').read().find(scraper.guid) > 0    
        except:
            # Don't risk running it twice
            return False


    def get_overdue_scrapers(self, limit=10):
        """
        Obtains a queryset of scrapers that should have already been run, we 
        will order these with the ones that have run least recently hopefully
        being near the top of the list.
        """
        scrapers = Scraper.objects.exclude(privacy_status="deleted").filter(run_interval__gt=0)
        scrapers = scrapers.extra(where=["(DATE_ADD(last_run, INTERVAL run_interval SECOND) < NOW() or last_run is null)"]).order_by('-last_run')
        return [ s for s in scrapers[0:limit] if not self.is_currently_running(s) ] 


    def run(self):
        """
        Create and manage the worker processes that we are going to use to hand out work to
        making sure we do any contentious access before we write anything to their queue.
        """
        
        # Load the settings from the config file (sigh) and take out the settings 
        # we are interested in
        configfile = '/var/www/scraperwiki/uml/uml.cfg'

        config = ConfigParser.ConfigParser()        
        with open(configfile, 'r') as configfile:
            config.readfp(configfile)
        
        queue = Queue()
        
        # Prefetch any interesting properties from the configuration file
        config_dict = {
            'dhost'   : config.get('dispatcher', 'host'),
            'dport'   : config.getint('dispatcher', 'port'),
            'confurl' : config.get('dispatcher', 'confurl'),
        }
        
        # Setup the processes we want to have waiting for jobs to do.
        self.processes = []
        for px in range(10):
            p = Process(target=subprocessor, args=(queue,config_dict))
            p.start()
            
            self.processes.append(p)

        
        while True:
            scrapers = self.get_overdue_scrapers()
            if len(scrapers) == 0:
                logging.debug( 'Sleeping as there is nothing to do' )
                time.sleep(30)
                
            for scraper in scrapers:
                queue.put( {'scraper': scraper.id, 'task': 'run'}, block=True, timeout=None ) # put scraper ID
                                
        for p in self.processes:
            logging.debug( 'Joining %s' % p )
            p.join(1)
            
        logging.shutdown()


if __name__ == '__main__':
    """
    Entry point
    """
    formatter = logging.Formatter('%(asctime)-15s:  %(message)s')
    
    handler = MultiProcessingLog('/var/log/scraperwiki/scheduler.log', "a", 512*1024, 5)
    handler.setFormatter( formatter )
    
    root_logger = logging.getLogger()

    if len(sys.argv) == 2 and sys.argv[1] == 'debug':
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter( formatter )
        root_logger.addHandler( stream_handler )
        root_logger.setLevel( logging.DEBUG )        
    else:
        root_logger.setLevel( logging.WARNING )        
        
    root_logger.addHandler( handler  )
            
    root_logger.info( 'Scheduler running on pid %s' % os.getpid() )
    scheduler = Scheduler()
    scheduler.run()
    

