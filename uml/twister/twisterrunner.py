from twisted.internet import protocol, utils, reactor
from twisted.web.client import Agent, ResponseDone
from twisted.internet.defer import succeed, Deferred
from twisted.internet.defer import Deferred
from twisted.internet.error import ProcessDone

import sys
import os
import datetime
import time
import uuid
import urllib, urlparse

try:    import json
except: import simplejson as json

def jstime(dt):
    return str(1000*int(time.mktime(dt.timetuple()))+dt.microsecond/1000)



class spawnRunner(protocol.ProcessProtocol):
    def __init__(self, client, code, logger):
        self.client = client
        self.code = code
        self.runID = None
        self.umlname = ''
        self.buffer = ''
        self.logger = logger
        self.style = "OldSpawnRunner"
        
    def connectionMade(self):
        self.logger.debug("Starting run "+self.style)
        if self.style == "OldSpawnRunner":
            self.transport.write(self.code)
            self.transport.closeStdin()
    
    def gotcontrollerconnectionprotocol(self, controllerconnection):
        controllerconnection.srunner = self
        self.controllerconnection = controllerconnection

        json_msg = json.dumps({'message_type': 'executionstatus', 'content': 'startingrun', 'runID': self.jdata["runid"], 'uml': "directcontroller"})
        self.outReceived(json_msg+'\n')
        
        sdata = json.dumps(self.jdata)
        self.logger.debug("sending: "+sdata)
        controllerconnection.transport.write('POST /Execute HTTP/1.1\r\n')
        controllerconnection.transport.write('Content-Length: %s\r\n' % len(sdata))
        controllerconnection.transport.write('Content-Type: text/json\r\n')
        controllerconnection.transport.write('Connection: close\r\n')
        controllerconnection.transport.write("\r\n")
        controllerconnection.transport.write(sdata)

    # messages from the UML
    def outReceived(self, data):
        self.logger.debug("runner to client# %d %s" % (self.client.clientnumber, data[:180]))
            # although the client can parse the records itself, it is necessary to split them up here correctly so that this code can insert its own records into the stream.
        lines  = (self.buffer+data).split("\n")
        self.buffer = lines.pop(-1)  # usually an empty
        
        for line in lines:
            if not self.runID:  # intercept the first record to record its state and add in further data
                try:
                    parsed_data = json.loads(line.strip("\r"))
                except:
                    # If this is X:Y then it may be a HTTP header and we should probably just ignore it
                    # although we could do with a proper http request.
                    continue
                
                if parsed_data.get('message_type') == 'executionstatus' and parsed_data.get('content') == 'startingrun':
                    self.runID = parsed_data.get('runID')
                    self.umlname = parsed_data.get('uml')
                    parsed_data['chatname'] = self.client.chatname
                    parsed_data['nowtime'] = jstime(datetime.datetime.now())
                    line = json.dumps(parsed_data)  # inject values into the field
            self.client.writeall(line)

        # could move into a proper function in the client once slimmed down slightly
    def processEnded(self, reason):
        self.client.processrunning = None

        sreason = str([reason])
        if sreason == "[<twisted.python.failure.Failure <class 'twisted.internet.error.ProcessDone'>>]":
            sreason = ""  # seems difficult to find the actual class type to compare with, but get rid of this "error" that really isn't an error
        elif sreason == "[<twisted.python.failure.Failure <class 'twisted.internet.error.ConnectionDone'>>]":
            sreason = ""  # seems difficult to find the actual class type to compare with, but get rid of this "error" that really isn't an error

        # other errors (eg connection lost) could put more useful errors into the client
        self.logger.debug("run process %s ended client# %d %s" % (self.client.clienttype, self.client.clientnumber, sreason))
    
        self.client.writeall(json.dumps({'message_type':'executionstatus', 'content':'runfinished', 'contentextra':sreason}))
        
        if self.client.clienttype == "editing":
            self.client.factory.notifyMonitoringClients(self.client)
        elif self.client.clienttype == "scheduledrun":
            self.client.scheduledrunmessageloophandler.schedulecompleted()
            self.client.factory.scheduledruncomplete(self.client, reason.type==ProcessDone)



# simply ciphers through the two functions
class ControllerConnectionProtocol(protocol.Protocol):
    def connectionLost(self, reason):
        #self.srunner.logger.debug("*** controller socket connection lost: "+str(reason))
        self.srunner.processEnded(reason)
        
    def dataReceived(self, data):
        #self.srunner.logger.debug("*** controller socket connection data: "+data)
        self.srunner.outReceived(data)
        
clientcreator = protocol.ClientCreator(reactor, ControllerConnectionProtocol)

# used for the process of direct connection to the controller through a socket
controllerhost = None
controllerport = None
def SetControllerHost(config):
    global controllerhost
    global controllerport
    umls = config.get('dispatcher', 'umllist').split(',')
    uname = umls[0]
    controllerhost = config.get(uname, 'host')
    controllerport = config.getint(uname, 'via')


# this is the new way that totally bypasses the dispatcher.  
# we reuse the spawnRunner class only for its user defined functions, not its processprotocol functions!
def MakeSocketRunner(scrapername, guid, language, urlquery, username, code, client, logger, user=None):
    srunner = spawnRunner(client, code, logger)  # reuse this class and its functions
    
    jdata = { }
    jdata["code"] = code.replace('\r', '')
    jdata["cpulimit"] = 80
    jdata["draft"] = (not username)
    jdata["language"] = language
    jdata["scraperid"] = guid
    jdata["urlquery"] = urlquery
    jdata["scrapername"] = scrapername
    jdata["beta_user"] = (user is not None and user.get('beta_user', False))

    # set the runid
    jdata["runid"] = '%.6f_%s' % (time.time(), uuid.uuid4())
    if jdata.get("draft"):
       jdata["runid"] = "draft|||%s" % jdata["runid"]

    srunner.jdata = jdata
    srunner.style = "NewSpawnRunner"
    srunner.pid = "NewSpawnRunner"  # for the kill_run function

    deferred = clientcreator.connectTCP(controllerhost, controllerport)
    deferred.addCallback(srunner.gotcontrollerconnectionprotocol)

    return srunner
    

def MakeRunner(scrapername, guid, language, urlquery, username, code, client, logger, user=None):
    beta_user = False
    try:
        if user is not None and user.get('beta_user',False):
            beta_user = True
    except:
        pass

    if beta_user:
        return MakeSocketRunner(scrapername, guid, language, urlquery, username, code, client, logger, user)

    args = ['./firestarter/runner.py']
    args.append('--guid=%s' % guid)
    args.append('--language=%s' % language)
    args.append('--name=%s' % scrapername)
    args.append('--urlquery=%s' % urlquery)
    if beta_user:
        args.append('--beta_user')
    if not username:
        args.append('--draft')

    code = code.encode('utf8')
    args = [i.encode('utf8') for i in args]
    logger.debug("./firestarter/runner.py: %s" % args)

    # from here we should somehow get the runid
    return reactor.spawnProcess(spawnRunner(client, code, logger), './firestarter/runner.py', args, env={'PYTHON_EGG_CACHE' : '/tmp'})
