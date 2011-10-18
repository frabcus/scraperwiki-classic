"""
Datastore.py

A server that handles incoming connections to various Sqlite databases that 
are stored on disk and access over a network.
"""
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from datalib import SQLiteDatabase
import uuid

class DatastoreProtocol(basic.LineReceiver):
    """
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialise the local attributes that we want
        """
        self.read_header = False
        
        
    def lineReceived(self, line):
        """
        Handles incoming lines of text (correctly separated) these,
        after the http headers will be JSON which expect a JSON response
        """
        # See if we have read all of the HTTP header yet.
        # Store what we need to store for this client 
        # connection
        if not self.read_header and line == '':
            self.read_header = True
            return
            
        if self.read_header:
            # We can process the JSON request that is defined in 'line'
            pass
        else:
            # This is still a HTTP header .. proto? K:V?
            pass
            

class DatastoreFactory( protocol.ServerFactory ):
    protocol = DatastoreProtocol
    
    
if __name__ == '__main__':
    reactor.listenTCP( 2112, DatastoreFactory())
    reactor.run()