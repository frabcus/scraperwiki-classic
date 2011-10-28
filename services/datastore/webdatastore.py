"""
Webdatastore.py

"""
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.protocols import basic
from twisted.internet import defer
from twisted.internet.threads import deferToThread
from twisted.web import server, resource, http

from datalib import SQLiteDatabase

import ConfigParser, logging, cgi
import re, uuid, urlparse
import json, time, sys

form = """\
<html><body>
<form action='.' method='POST'>
    <label for='scrapername'>Scraper Name</label>
    <input type='text' name='scrapername' size='30'/><br/>

    <label for='runid'>Run ID</label>
    <input type='text' name='runid' size='30'/><br/>
    
    <label for='command'>Command</label>    
    <textarea name='command' rows='10' cols='30'></textarea><br/>
    <input type='submit' value='send'/>
</form>
</html>\
"""

class WebDatastoreResource(resource.Resource):
    """
    
    """
    
    isLeaf=True


    def _error(self, failure, request ):
        d = defer.Deferred()
        request.notifyFinish().addCallback(self._write, d, {"Error": "There was a problem with the request"} )
    
    
    def _write(self, data, request ):
        """
        Writes the response out to the client
        """
        request.setResponseCode(http.OK)
        request.write( data )
        request.finish()       


    def check_hash(self, request, name):
        """
 secret_key = '%s%s' % (self.short_name, self.factory.secret,)
                possibly = hashlib.sha256(secret_key).hexdigest()  
                log.msg( 'Comparing %s == %s' % (possibly, self.headers['X-Scraper-Verified'],) , 
                         logLevel=logging.DEBUG)      
                                                                                                        
                if not possibly == self.headers['X-Scraper-Verified']:
                    self.write_fail('Permission refused')
                    return        
        """
        return False
        

    def process(self, request):
        """
        
        """
        db = None
        try:
            log.msg( 'Processing request', logLevel=logging.DEBUG )
        
            scrapername = cgi.escape( request.args.get('scrapername', [''])[0] )
            runid = cgi.escape( request.args.get('runid', [''])[0] )            
            command = cgi.escape( request.args.get('command', [''])[0] )         
            attachables = map( cgi.escape, request.args.get('attachables', []) )
        
            if command == "":
                raise Exception("No command was supplied")
                
            if not self.check_hash(request, scrapername):
                raise Exception("Permission check failed")                
        
            dataauth = "fromfrontend"
            if runid[:8] == "draft|||" and scrapername:
                dataauth = "draft"
            else:
                dataauth = "writable"        
        
            # Create the database and pass the request to it.
            db = SQLiteDatabase(self, '/var/www/scraperwiki/resourcedir', scrapername, dataauth, runid, attachables)                                
        
            return "HellO!"
        except Exception, e:
            log.err( e )
            return '{"Error": "%s"}' % e.message
        finally:
            if db:
                db.close()

    def render_GET(self, request):
        return form
                
    def render_POST(self, request):
        d = deferToThread( self.process, request)
        d.addCallback(self._write, request)
        d.addErrback(self._error, request)
        return server.NOT_DONE_YET


    
###############################################################################
# Init
###############################################################################
    
# Load the config file from the usual place.
configfile = '/var/www/scraperwiki/uml/uml.cfg'
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

