"""
datarouter.py

A server routes client connections to datastore instances on the same machine (for now)
allowing us to have one per CPU

Things to check/do:
 - We use deferToThread() for sqlite, can this be optimised with twisted dbapi?
 - Can we better handle huge lines of content?
 - Remove the partial HTTP, either go full HTTP or remove it.
 
"""
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.protocols import basic
from twisted.internet import defer
from twisted.internet.endpoints import TCP4ClientEndpoint

import ConfigParser, logging
import re, uuid, urlparse
import json, time, sys

class ForwardingProtocol(protocol.Protocol):
    
    router = None
    
    def __init__(self):
        pass    
        
    def connectionLost(self, reason):
        self.transport.loseConnection()
        if self.router:
            self.router.transport.loseConnection()
                
    def sendMessage(self, msg):
        self.transport.write(msg)
                
    def dataReceived(self, data):
        self.router.transport.write( data )
        
        

class DatarouterProtocol(basic.LineReceiver):

    def __init__(self):
        self.connection = None
                        
    def connectionMade(self):
        self.host,self.port = self.factory.choose_instance()
        log.msg( "Instance set to %s:%d" % (self.host, self.port) , logLevel=logging.DEBUG )

        self.factory = protocol.Factory()
        self.factory.protocol = ForwardingProtocol
        self.point = TCP4ClientEndpoint(reactor, self.host, self.port)                              
        self.fwd = self.point.connect(self.factory)
        self.fwd.addCallback(self.ready)        

    def ready(self, connection):
        self.connection = connection
        self.connection.router = self
        
    def lineLengthExceeded(self, line):
        """
        Handle the maximum line length limit being met, and don't even forward the 
        request.
        
        TODO: When more than 262144 bytes is sent, we should let the user know there 
              was a problem
        """
        self.sendLine(  '{"error": "Buffer size exceeded, please send less data on each request"}'  )
        

    def lineReceived(self, line):
        """
        Handles incoming lines of text (correctly separated) these,
        after the http headers will be JSON which expect a JSON response
        """
        log.msg('Received: ' + line)
        # TODO: If self.connection is None then we are not connection to a datastore
        self.connection.sendMessage(line + "\n")
        log.msg('Sent: ' + line)        
            
            
    def connectionLost(self, reason):
        """
        Called when the connection was lost, we should clean up the DB here
        by closing the connection we have to it.
        """
        if self.connection:
            self.connection.router = None
            self.connection.transport.loseConnection()
            
        log.msg( "Closing connection to %s:%d" % (self.host, self.port) , logLevel=logging.DEBUG )

    
class DatarouterFactory( protocol.ServerFactory ):
    protocol = DatarouterProtocol
    
    instances = []
    last_used = 0

    def __init__(self):
        self.instances = None
    
    def set_instances(self):
        self.instances = []
        for l in [x.strip() for x in config.get( 'datarouter', 'stores' ).split(',')]:
            h,p = l.split(':')
            self.instances.append( (h,int(p),) )
        print self.instances
        

    def choose_instance( self ):
        """
        Does a round robin on all of the instances available and chooses which
        one to use.  We can replace this with something just as naive later on 
        to make sure certain short_names are routed to certain routers. Suggest
        memcached style arrangement (not the crc32(name) modulo solution)
        """
        if not self.instances:
            self.set_instances()
            
        if self.last_used >= len(self.instances):
            self.last_used = 0
        i = self.instances[self.last_used]
        self.last_used += 1
        return i
    
    
###############################################################################
# Init and run (locally)
###############################################################################
    
# Set the maximum line length and the line delimiter
DatarouterProtocol.delimiter = '\n'
DatarouterProtocol.MAX_LENGTH = 262144 # HUGE buffer

# Load the config file from the usual place.
configfile = '/var/www/scraperwiki/uml/uml.cfg'
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

if __name__ == '__main__':
    log.startLogging(sys.stdout)    
    df = DatarouterFactory()
    reactor.listenTCP( 9003, df)
    reactor.run()