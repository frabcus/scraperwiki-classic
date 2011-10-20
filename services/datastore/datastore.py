"""
Datastore.py

A server that handles incoming connections to various Sqlite databases that 
are stored on disk and accessed over a network. This datastore, like the old 
dataproxy still maintains a connection (per scraper run) and so forces commands 
in sequence.

Things to check/do:
 - We use deferToThread() for sqlite, can this be optimised with twisted dbapi?
 - Can we better handle huge lines of content?
 - Remove the partial HTTP, either go full HTTP or remove it.
 
"""
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.protocols import basic
from twisted.internet import defer
from twisted.internet.threads import deferToThread

from datalib import SQLiteDatabase

import ConfigParser, logging
import re, uuid, urlparse
import json, time, sys


###############################################################################
# Classes
###############################################################################


class DatastoreProtocol(basic.LineReceiver):
    """
    Basic LineReceiver implementation (as the protocol is line-at-a-time)
    
    For historical reasons this handles the initial handshake as a HTTP 
    request, and once initiated then treats it like a socket (without any
    headers being sent in the response). Each line received is expected to
    be a JSON string, which is then loaded and processed before returning
    the response, again as a JSON string. Each line sent and received is 
    delimited by \n.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialise the local attributes that we want
        """
        self.have_read_header = False
        self.headers = {}
        self.params = None
        self.action = None
        self.db     = None
        self.short_name,self.dataauth, self.runID, self.attachables = None, None, None, []
        
        
    def db_process_success(self, res):
        """
        Called on a successful database action, the data we are given is encoded and 
        then written as a line.  
        
        TODO: A more optimal solution might be to find out if json.dumps can write the
              output straight to the stream?
        """
        result = json.dumps( res )            
        if result:
            log.msg( result[:200], logLevel=logging.DEBUG )
        self.sendLine( result + "\n" )


    def db_process_error(self, failure):
        """
        A failed database action. This is likely to be an unhandled exception in
        the datalib so we really should return a valid response.
        """
        log.err( failure )
        #self.sendLine( result + "\n" )
        
        
    def process(self, obj):
        """ 
        Process the provided JSON obj (has already been converted to JSON)
        and make sure the response is sent with self.sendLine()
        """
        if self.db is None:
            # First pass through
            firstmessage = obj
            firstmessage["short_name"] = self.short_name
            firstmessage["runID"]      = self.runID
            firstmessage["dataauth"]   = self.dataauth
            log.msg( 'Ready to send response of ' + str(firstmessage), logLevel=logging.DEBUG )
            self.sendLine( json.dumps(firstmessage)  )
            self.db = SQLiteDatabase(self, '/var/www/scraperwiki/resourcedir', self.short_name, self.dataauth, self.runID, self.attachables)            
        else:
            # Second and subsequent connections (when we have DB) we will
            # defer to run in its own thread for a single activity on the db
            # class.  The next request may well be on another thread, but 
            # *currently* we force sequential access - this will need fixing 
            # when we have zero shared state.
            log.msg( 'Starting async call', logLevel=logging.DEBUG)                                                                     
            d = deferToThread( self.db.process, obj )
            d.addCallback( self.db_process_success )
            d.addErrback( self.db_process_error )
            

    def lineLengthExceeded(self, line):
        """
        TODO: When more than 64k is sent, we should let the user know there 
              was a problem
        """
        pass
        

    def lineReceived(self, line):
        """
        Handles incoming lines of text (correctly separated) these,
        after the http headers will be JSON which expect a JSON response
        """
        # See if we have read all of the HTTP header yet.
        # Store what we need to store for this client 
        # connection
        self.factory.connection_count += 1
        if not self.have_read_header and line.strip() == '':
            self.have_read_header = True
            line = '{"status": "good"}'
            log.msg( 'Finished reading headers', logLevel=logging.DEBUG)
                        
        if self.have_read_header:
            try:
                log.msg( 'Starting process message', logLevel=logging.DEBUG)                                                
                obj = json.loads(line)
                self.process( obj )       
            except Exception, e:
                log.err(e)
                
        else:
            log.msg( 'Parsing headers', logLevel=logging.DEBUG)
            if self.params is None:
                if not self.parse_params(line):
                    self.sendLine('500 Failed')
                    self.transport.loseConnection()
                    return
            else:
                k,v = line.split(':')
                self.headers[k.strip()] = v.strip()

            if 'short_name' in self.params:
                self.attachauthurl = config.get("dataproxy", 'attachauthurl')                
                self.short_name = self.params['short_name']
                self.runID = 'fromfrontend.%s.%s' % (self.short_name, time.time()) 
                self.dataauth = "fromfrontend"
            else:
                self.short_name  = self.params['vscrapername']
                self.runID       = self.params['vrunid']
                if self.runID[:8] == "draft|||" and self.short_name:
                    self.dataauth = "draft"
                else:
                    self.dataauth = "writable"
                    
            if 'attachables' in self.params:
                self.attachables = self.params['attachables']
            
            
    def connectionLost(self, reason):
        """
        Called when the connection was lost, we should clean up the DB here
        by closing the connection we have to it.
        """
        print 'Connection lost'
        if self.db:
            self.db.close()
            self.db = None


    def parse_params(self, line):
        """
        Parse the GET request and store the parameters we received.
        """
        log.msg( 'Parsing parameters',logLevel=logging.DEBUG)
        self.params = {}        
        m = re.match('GET /(.*) HTTP/(\d+).(\d+)', line)
        if not m:
            return
            
        qs = m.groups(0)[0]
        if '?' in qs:
            self.action = qs[ :qs.find('?') ]            
            qs = qs[ qs.find('?')+1: ]
        else:
            self.action = qs
            qs = None
    
        if qs:
            self.params.update( dict( [ p.split('=') for p in qs.split('&') ] ) )
            return True
        return False

    
class DatastoreFactory( protocol.ServerFactory ):
    protocol = DatastoreProtocol
    connection_count = 0
    
###############################################################################
# Init and run (locally)
###############################################################################
    
# Set the maximum line length and the line delimiter
DatastoreProtocol.delimiter = '\n'
DatastoreProtocol.MAX_LENGTH = 65536

# Load the config file from the usual place.
configfile = '/var/www/scraperwiki/uml/uml.cfg'
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))


if __name__ == '__main__':
    log.startLogging(sys.stdout)    
    reactor.listenTCP( 9003, DatastoreFactory())
    reactor.run()