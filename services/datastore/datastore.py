"""
Datastore.py

A server that handles incoming connections to various Sqlite databases that 
are stored on disk and access over a network.
"""
from twisted.internet import reactor, protocol
from twisted.protocols import basic
from twisted.internet import defer
from twisted.internet.threads import deferToThread

from datalib import SQLiteDatabase

import ConfigParser
import re, uuid, urlparse
import json, time

configfile = '/var/www/scraperwiki/uml/uml.cfg'
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

class DatastoreProtocol(basic.LineReceiver):
    """
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialise the local attributes that we want
        """
        self.have_read_header = False
        self.headers = {}
        self.params = None
        self.action = None
        self.db = None
        
        self.short_name,self.dataauth, self.runID, self.attachables = None, None, None, []
        
    def db_process_success(self, res):
        result = json.dumps( res )            
        if result:
            print result[:200]
        self.sendLine( result + "\n" )

    def db_process_error(self, failure):
        print failure
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
            print 'Ready to send response of ' + str(firstmessage)
            self.sendLine( json.dumps(firstmessage)  )
            #print 'Connecting to - ' + config.get('dataproxy', 'resourcedir')
            self.db = SQLiteDatabase(self, '/var/www/scraperwiki/resourcedir', self.short_name, self.dataauth, self.runID, self.attachables)            
        else:
            # Second and subsequent connections (when we have DB) we will
            # defer to run in its own thread for a single activity on the db
            # class.  The next request may well be on another thread, but 
            # *currently* we force sequential access - this will need fixing 
            # when we have zero shared state.
            d = deferToThread( self.db.process, obj )
            d.addCallback( self.db_process_success )
            d.addErrback( self.db_process_error )
            

        
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
                        
        if self.have_read_header:
            try:
                obj = json.loads(line)
                self.process( obj )                
            except Exception, e:
                print e
                
        else:
            print '- Parsing headers'            
            if self.params is None:
                self.parse_params(line)
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
        print '- Connection lost'
        if self.db:
            self.db.close()
            self.db = None


    def parse_params(self, line):
        """
        Parse the GET request and store the parameters we received.
        """
        print '- Parsing parameters'        
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

            
class DatastoreFactory( protocol.ServerFactory ):
    protocol = DatastoreProtocol
    
    connection_count = 0
    
    
if __name__ == '__main__':
    DatastoreProtocol.delimiter = '\n'
    print '- Listening'    
    reactor.listenTCP( 9003, DatastoreFactory())
    reactor.run()