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

varDir = './var'

# 'json' is only included in python2.6.  For previous versions you need to
# Install siplejson manually.
try:
  import json
except:
  import simplejson as json

from twisted.internet import protocol, utils, reactor, task
from twisted.protocols.basic import LineOnlyReceiver


# perhaps in-line this
def format_message(content, message_type='console'):
    return json.dumps({'message_type' : message_type, 'content' : content})


class LocalLineOnlyReceiver(LineOnlyReceiver):
    def lineReceived(self, line):
        if line != "":
            self.transport.write(line+",")

class spawnRunner(protocol.ProcessProtocol):
    def __init__(self, P, code):
        self.client = P
        self.code = code
        self.LineOnlyReceiver = LocalLineOnlyReceiver()
        self.LineOnlyReceiver.transport = self.client.transport
        self.LineOnlyReceiver.delimiter = "\r\n"
        self.LineOnlyReceiver.MAX_LENGTH = 1000000000000000000000
        self._buffer = ""
    

    def connectionMade(self):
        print "Starting run"
        self.transport.write(self.code)
        self.transport.closeStdin()
        self.client.write(format_message("Starting scraper ..."))
        
    def outReceived(self, data):
        print data
        self.LineOnlyReceiver.dataReceived(data)


    def processEnded(self, data):
        # self.client.write('')
        # data = format_message('Finished', 'kill')
        self.client.kill_run(reason="OK")
        print "run ended"
        

# There's one of these per editor window open.  All connecting to same factory
class RunnerProtocol(protocol.Protocol):
     
    def __init__(self):
        # Set if a run is currently taking place, to make sure we don't run 
        # more than one scraper at a time.
        self.running = False
            
    def connectionMade(self):
        self.factory.clientConnectionMade(self)
        print "new connection", len(self.factory.clients)
    
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
            if parsed_data['command'] == "kill" and self.running:
                # Kill the running process
                self.kill_run('clientKilled')
                
            elif parsed_data['command'] == 'run' and not self.running:
                if 'code' in parsed_data:
                    code = parsed_data['code']
                    code = code.encode('utf8')
                    
                    guid = parsed_data['guid']
                    args = ['./firestarter/runner.py']
                    args.append('-g %s' % guid)
                    
                    # args must be an ancoded string, not a unicode object
                    args = [i.encode('utf8') for i in args]

                    self.running = reactor.spawnProcess(
                        spawnRunner(self, code), \
                        './firestarter/runner.py', args
                            )

                else:
                    raise ValueError('++?????++ Out of Cheese Error. Redo From Start: `code` to run not specified')
                    
        except Exception, e:
            self.transport.write(format_message("Command not valid (%s)" % e))

    def write(self, line, formatted=True):
        """
        A simple method that writes `line` back to the client.
        
        We assume that `line` has been formatted correctly at some stage 
        before.
        """
        self.transport.write(line)
    
    def kill_run(self, reason='connectionLost'):
        try:
            os.kill(self.running.pid, signal.SIGKILL)
        except:
            pass
        self.running = False
        
        if reason == 'clientKilled':
            self.write(json.dumps({'message_type' : 'kill', 'content' : 'Script cancelled'}))
        elif reason == "OK":
            self.write(json.dumps({'message_type' : 'kill', 'content' : 'Script successful'}))
        else:
            self.write(json.dumps({'message_type' : 'kill', 'content' : 'Script cancelled'}))
            
    def connectionLost(self, reason):
        """
        Called when the connection is shut down.
        
        Kills and running spawnRunner processes.
        """
        self.factory.clientConnectionLost(self)
        print "end connection", len(self.factory.clients), reason
        
        self.kill_run(reason='connectionLost')


class RunnerFactory(protocol.ServerFactory):
    protocol = RunnerProtocol
    
    def __init__(self):
        self.clients = []
        self.announcecount = 0
        self.lc = task.LoopingCall(self.announce)
        self.lc.start(10)

    # every 10 seconds sends out a quiet poll
    def announce(self):
        self.announcecount += 1
        for client in self.clients:
            res = []
            for c in self.clients:
                res.append(c == self.clients and "T" or "-")
                res.append(c.running and "R" or ".")
            client.write(format_message("%d c %d clients, running:%s" % (self.announcecount, len(self.clients), "".join(res))))

    def clientConnectionMade(self, client):
        self.clients.append(client)

    def clientConnectionLost(self, client):
        self.clients.remove(client)


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
