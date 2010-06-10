#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

"""
This script is the interface between the UML/firebox set up and the frontend 
Orbited TCP socket.  

When a connection is made RunnerProtocol listens for data coming from the 
client.  This can be anything


class RunnerProtocol(protocol.Protocol):
class RunnerFactory(protocol.ServerFactory):
    protocol = RunnerProtocol

class spawnRunner(protocol.ProcessProtocol)

"""

import sys
import os
import signal
import time
from optparse import OptionParser
import ConfigParser
import urllib2
import urllib      #  do some asynchronous calls

varDir = './var'

# 'json' is only included in python2.6.  For previous versions you need to
# Install siplejson manually.
try:
  import json
except:
  import simplejson as json

from twisted.internet import protocol, utils, reactor, task
from twisted.protocols.basic import LineOnlyReceiver

# for calling back to the scrapers/twister/status
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
agent = Agent(reactor)

# the comma is added into format_message and LineOnlyReceiver because lines may be batched and 
# they are decoded in editor.js by attempting to evaluate the json string '['+receiveddata+']'

# perhaps in-line this
def format_message(content, message_type='console'):
    return json.dumps({'message_type' : message_type, 'content' : content})

# the messages of the type given by format_message also get generated by firestarter/runner.py
# and are passed through lineReceived.  Look there fore further formatting information.
# things like exception parsing is done all the way in the controller.py

# I think this class is only only for chunking into lines
# see http://twistedmatrix.com/documents/8.2.0/api/twisted.protocols.basic.LineOnlyReceiver.htm

class LocalLineOnlyReceiver(LineOnlyReceiver):
    def lineReceived(self, line):
        if line != "":
            self.client.writeall(line)

# the streaming data from the runner gets chunked into lines so that twister can 
# insert its own messages into the same transport stream
# it would be more efficient to stream it over completely, because editor.js 
# is capable of finding the line feeds itself.
# for now it's separated by commas. (can see the advantage of string.splitlines leaving the trailing linefeeds)

class spawnRunner(protocol.ProcessProtocol):
    def __init__(self, client, code):
        self.client = client
        self.code = code
        self.LineOnlyReceiver = LocalLineOnlyReceiver()
        self.LineOnlyReceiver.transport = self.client.transport
        self.LineOnlyReceiver.client = self.client
        self.LineOnlyReceiver.delimiter = "\r\n"  # this delimeter is inserted in runner.py line 61
        self.LineOnlyReceiver.MAX_LENGTH = 1000000000000000000000
        self._buffer = ""
    

    def connectionMade(self):
        print "Starting run"
        self.transport.write(self.code)
        self.transport.closeStdin()
        startmessage = json.dumps({'message_type' : "startingrun", 'content' : "starting run"})
        #startmessage = format_message("starting run", message_type="startingrun")  # adds a comma
        self.client.writeall(startmessage)
        
    # see http://twistedmatrix.com/documents/10.0.0/api/twisted.internet.protocol.ProcessProtocol.html
    # reroutes this into LineOnlyReceiver to chunk into lines
    def outReceived(self, data):
        print "out", data
        self.LineOnlyReceiver.dataReceived(data)  # this batches it up into line feeds


    def processEnded(self, data):
        # self.client.write('')
        # data = format_message('Finished', 'kill')
        self.client.kill_run(reason="OK")
        print "run ended"
        

# There's one of these per editor window open.  All connecting to same factory
# this is usually called client
class RunnerProtocol(protocol.Protocol):
     
    def __init__(self):
        # Set if a run is currently taking place, to make sure we don't run 
        # more than one scraper at a time.
        self.running = False
        self.guid = ""
        self.scrapername = ""
        self.isstaff = False
        self.username = ""
        self.userrealname = ""
        self.chatname = ""
        self.clientnumber = -1  # for whole operation of twisted
        self.scrapereditornumber = -1  # out of all people editing a particular scraper
        

    def connectionMade(self):
        self.factory.clientConnectionMade(self)
        print "new connection", len(self.factory.clients)
        # we don't know what scraper they've actually opened until we get the dataReceived
        
    def dataReceived(self, data):
        """
        Listens for data coming from the client.
        
        When new data is received it's parsed in to a JSON object and parsed.
        If this fails an exception is raised and a message is written to the 
        client.
        
        The parsed JSON object must contain a `command` key with a value of:
        
            - `run`: Run the code contained in the `code` key.  This command
                     is not valid without accompioning `code` key.

            - `kill`: Sends SIGKILL to the `spawnRunner` process for this 
                      client.  No other keys are required.
        
        If `command` is 'run' and the `code` key exists, reactor.spawnProcess
        is called with spawnRunner as an argument.  
        
        'spawnProcess' calls an object that interfaces with a command in a 
        new thread.  'Interfaces' here referes to reading and writing to the
        file descriptiors.  See the spawnRunner documentation for more.
        """

        try:
            parsed_data = json.loads(data)
            if parsed_data['command'] == "kill":
                # Kill the running process (or other if staff)
                if self.running:
                    self.kill_run('clientKilled')
                
                # someone who didn't start it going hits kill
                elif self.isstaff:
                    for client in self.factory.clients:
                        if client.guid == self.guid and client.running:
                            client.kill_run('clientKilled')
                
            elif parsed_data['command'] == 'run' and not self.running:
                if 'code' in parsed_data:
                    code = parsed_data['code']
                    code = code.encode('utf8')
                    
                    # these could all be fetched from self
                    guid = parsed_data['guid']
                    scraperlanguage = parsed_data.get('language', 'Python')
                    scrapername = parsed_data.get('scrapername', '')
                    scraperlanguage = parsed_data.get('language', '')

                    assert guid == self.guid
                    args = ['./firestarter/runner.py']
                    args.append('--guid=%s' % guid)
                    args.append('--language=%s' % scraperlanguage)
                    args.append('--name=%s' % scrapername)
                    
                    # args must be an ancoded string, not a unicode object
                    args = [i.encode('utf8') for i in args]

                    print "./firestarter/runner.py: %s" % args

                    self.running = reactor.spawnProcess(
                        spawnRunner(self, code), \
                        './firestarter/runner.py', args, env={'PYTHON_EGG_CACHE' : '/tmp'}
                            )

                    message = "%s runs scraper" % self.chatname
                    if self.guid:
                        self.factory.sendchatmessage(self.guid, message, None)
                    else:   
                        self.write(format_message(message, message_type='chat'))  # write it back to itself
                
                else:
                    raise ValueError('++?????++ Out of Cheese Error. Redo From Start: `code` to run not specified')
                    
            elif parsed_data['command'] == 'connection_open':
                self.guid = parsed_data['guid']
                self.username = parsed_data['username']
                self.userrealname = parsed_data.get('userrealname', self.username)
                self.scrapername = parsed_data.get('scrapername', '')
                self.scraperlanguage = parsed_data.get('language', '')
                self.isstaff = (parsed_data.get('isstaff') == "yes")
                
                if self.userrealname:
                    self.chatname = self.userrealname
                else:
                    self.chatname = "Anonymous%d" % self.factory.anonymouscount
                    self.factory.anonymouscount += 1
                    
                if self.guid:
                    editorclients = self.factory.updatescrapereditornumber(self.guid)
                    self.factory.sendchatmessage(self.guid, "%s enters" % self.chatname, self)
                    if self in editorclients:
                        editorclients.remove(self)
                        if editorclients:
                            message = "Other editors: %s" % ", ".join([lclient.chatname  for lclient in editorclients ])
                            self.write(format_message(message, message_type='chat'))  # write it back to itself
                
                self.factory.notifytwisterstatus()
        
            
            elif parsed_data['command'] == 'saved':
                line = json.dumps({'message_type' : "saved", 'content' : "%s saved" % self.chatname})
                otherline = json.dumps({'message_type' : "othersaved", 'content' : "%s saved" % self.chatname})
                self.writeall(line, otherline)

            elif parsed_data['command'] == 'chat':
                message = "%s: %s" % (self.chatname, parsed_data['text'])
                
                if self.guid:
                    self.factory.sendchatmessage(self.guid, message, None)
                
                # unsaved scraper case (just talking to self)
                else:   
                    self.write(format_message(message, message_type='chat'))  # write it back to itself
        
        
        except Exception, e:
            self.transport.write(format_message("Command not valid (%s)  %s " % (e, data)))


    
    def write(self, line, formatted=True):
        """
        A simple method that writes `line` back to the client.
        
        We assume that `line` has been formatted correctly at some stage 
        before.
        """
        self.transport.write(line+",\r\n")  # note the comma added to the end for json parsing when strung together
    
    def writeall(self, line, otherline=""):
        self.write(line)  
        
        if not otherline:
            otherline = line
        
        # send any destination output to any staff who are watching
        for client in self.factory.clients:
            if client.guid == self.guid and client != self and client.isstaff:
                client.write(otherline)  
    
    def kill_run(self, reason='connectionLost'):
        try:
            os.kill(self.running.pid, signal.SIGKILL)
        except:
            pass
        self.running = False
        
        if reason == 'clientKilled':
            self.writeall(json.dumps({'message_type' : 'kill', 'content' : 'Script cancelled'}))
        elif reason == "OK":
            self.writeall(json.dumps({'message_type' : 'end', 'content' : 'Script successful'}))
        else:
            self.writeall(json.dumps({'message_type' : 'kill', 'content' : 'Script cancelled'}))
        self.factory.notifytwisterstatus()


    def connectionLost(self, reason):
        """
        Called when the connection is shut down.
        
        Kills and running spawnRunner processes.
        """
        if self.guid:
            self.factory.sendchatmessage(self.guid, "%s leaves" % self.chatname, self)
        self.factory.clientConnectionLost(self)
        print "end connection", len(self.factory.clients), reason
        if self.guid:
            self.factory.updatescrapereditornumber(self.guid)
        self.factory.notifytwisterstatus()
        
        if self.running:
            self.kill_run(reason='connectionLost')


class RunnerFactory(protocol.ServerFactory):
    protocol = RunnerProtocol
    
    def __init__(self):
        self.clients = []
        self.clientcount = 0
        self.anonymouscount = 1
        self.announcecount = 0
        
        # set the visible heartbeat going
        #self.lc = task.LoopingCall(self.announce)
        #self.lc.start(10)

        self.m_conf        = ConfigParser.ConfigParser()
        config = '/var/www/scraperwiki/uml/uml.cfg'
        self.m_conf.readfp (open(config))
        self.twisterstatusurl = self.m_conf.get('twister', 'statusurl')
        
        self.notifytwisterstatus()

    # every 10 seconds sends out a quiet poll
    def announce(self):
        self.announcecount += 1
        for client in self.clients:
            res = []
            for c in self.clients:
                res.append(c == client and "T" or "-")
                res.append(c.running and "R" or ".")
            client.write(format_message("%d c %d clients, running:%s" % (self.announcecount, len(self.clients), "".join(res)), message_type='chat'))


# could get rid of this and replace everywhere with writeall

    def sendchatmessage(self, guid, message, nomessageclient):
        for client in self.clients:
            if client.guid == guid and client != nomessageclient and client.isstaff:
                client.write(format_message(message, message_type='chat'))
        
    # yes I know this would all be better as a dict from scrapers to lists of clients
    def updatescrapereditornumber(self, guid):
        editorclients = []
        lscrapereditornumber = 0
        for client in self.clients:
            if client.guid == guid:
                client.scrapereditornumber = lscrapereditornumber
                lscrapereditornumber += 1
                editorclients.append(client)
        return editorclients


    def clientConnectionMade(self, client):
        client.clientnumber = self.clientcount
        self.clients.append(client)
        self.clientcount += 1

    def clientConnectionLost(self, client):
        self.clients.remove(client)

    def notifytwisterstatus(self):
        clientlist = [ { "clientnumber":client.clientnumber, "guid":client.guid, "username":client.username, "running":bool(client.running)}   for client in self.clients ]
        data = { "value": json.dumps({'message_type' : "currentstatus", 'clientlist':clientlist}) }
        
        # achieves the same as below, but causing the system to wait for response
        #d = urllib2.urlopen(self.twisterstatusurl, urllib.urlencode(data)).read()
        
        # uses a GET due to not knowing how to use POST and send stuff
        #  http://twistedmatrix.com/documents/current/web/howto/client.html
        #print "Notifying status", data
        d = agent.request('GET', "%s?%s" % (self.twisterstatusurl, urllib.urlencode(data)), Headers({'User-Agent': ['Scraperwiki Twisted']}), None)

        
        

def execute (port) :
    
    reactor.listenTCP(port, RunnerFactory())
    reactor.run()   # this function never returns


def sigTerm (signum, frame) :

    try    : os.kill (child, signal.SIGTERM)
    except : pass
    try    : os.remove (varDir + '/run/twister.pid')
    except : pass
    sys.exit (1)


if __name__ == "__main__":
    
    parser = OptionParser()

    parser.add_option("-p", "--port", dest="port", action="store", type='int',
                      help="Port that receives connections from orbited.",  
                      default=9010, metavar="port no (int)")
    parser.add_option("-v", "--varDir", dest="varDir", action="store", type='string',
                      help="/var directory for logging and pid files",  
                      default="/var", metavar="/var directory (string)")
    parser.add_option("-s", "--subproc", dest="subproc", action="store_true",
                      help="run in subprocess",  
                      default=False, metavar="run in subprocess")
    parser.add_option("-d", "--daemon", dest="daemon", action="store_true",
                      help="run as daemon",  
                      default=False, metavar="run as daemon")
    parser.add_option("-u", "--uid", dest="uid", action="store", type='int',
                      help="run as specified user",  
                      default=None, metavar="run as specified user")
    parser.add_option("-g", "--gid", dest="gid", action="store", type='int',
                      help="run as specified group",  
                      default=None, metavar="run as specified group")

    (options, args) = parser.parse_args()
    varDir = options.varDir

    #  If executing in daemon mode then fork and detatch from the
    #  controlling terminal. Basically this is the fork-setsid-fork
    #  sequence.
    #
    if options.daemon :

        if os.fork() == 0 :
            os .setsid()
            sys.stdin  = open ('/dev/null')
            sys.stdout = open (options.varDir + '/log/twister', 'w', 0)
            sys.stderr = sys.stdout
            if os.fork() == 0 :
                ppid = os.getppid()
                while ppid != 1 :
                    time.sleep (1)
                    ppid = os.getppid()
            else :
                os._exit (0)
        else :
            os.wait()
            sys.exit (1)

        pf = open (options.varDir + '/run/twister.pid', 'w')
        pf.write  ('%d\n' % os.getpid())
        pf.close  ()

    if options.gid is not None : os.setregid (options.gid, options.gid)
    if options.uid is not None : os.setreuid (options.uid, options.uid)
    
    #  If running in subproc mode then the server executes as a child
    #  process. The parent simply loops on the death of the child and
    #  recreates it in the event that it croaks.
    #
    if options.subproc :

        signal.signal (signal.SIGTERM, sigTerm)

        while True :

            child = os.fork()
            if child == 0 :
                time.sleep (1)
                break

            sys.stdout.write("Forked subprocess: %d\n" % child)
            sys.stdout.flush()
    
            os.wait()

    execute (options.port)
