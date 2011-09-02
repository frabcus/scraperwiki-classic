from twisted.internet import protocol, utils, reactor
from twisted.web.client import Agent, ResponseDone
from twisted.internet.defer import succeed, Deferred
from twisted.internet.defer import Deferred
from twisted.internet.error import ProcessDone

import sys
import os
import datetime
import time
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
    
    def connectionMade(self):
        self.logger.debug("Starting run")
        self.transport.write(self.code)
        self.transport.closeStdin()
    
    # messages from the UML
    def outReceived(self, data):
        self.logger.debug("runner to client# %d %s" % (self.client.clientnumber, data[:100]))
            # although the client can parse the records itself, it is necessary to split them up here correctly so that this code can insert its own records into the stream.
        lines  = (self.buffer+data).split("\r\n")
        self.buffer = lines.pop(-1)  # usually an empty
        
        for line in lines:
            if not self.runID:  # intercept the first record to record its state and add in further data
                parsed_data = json.loads(line)
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
        self.client.writeall(json.dumps({'message_type':'executionstatus', 'content':'runfinished'}))
        
        if self.client.clienttype == "editing":
            self.client.factory.notifyMonitoringClients(self.client)
        elif self.client.clienttype == "scheduledrun":
            self.client.scheduledrunmessageloophandler.schedulecompleted()
            self.client.factory.scheduledruncomplete(self.client, reason.type==ProcessDone)

        sreason = str([reason])
        if sreason == "[<twisted.python.failure.Failure <class 'twisted.internet.error.ProcessDone'>>]":
            sreason = ""  # seems difficult to find the actual class type to compare with, but get rid of this "error" that really isn't an error

        self.logger.debug("run process %s ended client# %d %s" % (self.client.clienttype, self.client.clientnumber, sreason))


def MakeRunner(scrapername, guid, language, urlquery, username, code, client, logger, user=None):
    args = ['./firestarter/runner.py']
    args.append('--guid=%s' % guid)
    args.append('--language=%s' % language)
    args.append('--name=%s' % scrapername)
    args.append('--urlquery=%s' % urlquery)
    try:
        if user is not None and user.get('beta_user',False):
            args.append('--beta_user')
    except:
        pas
    if not username:
        args.append('--draft')

    code = code.encode('utf8')
    args = [i.encode('utf8') for i in args]
    logger.debug("./firestarter/runner.py: %s" % args)

    # from here we should somehow get the runid
    return reactor.spawnProcess(spawnRunner(client, code, logger), './firestarter/runner.py', args, env={'PYTHON_EGG_CACHE' : '/tmp'})
