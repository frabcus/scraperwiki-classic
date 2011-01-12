#!/bin/sh -
"exec" "python" "-O" "$0" "$@"

"""
This script is the interface between the UML/firebox set up and the frontend Orbited TCP socket.  

There is one client object (class RunnerProtocol) per editor window
These recieve and send all messages between the browser and the UML
An instance of a scraper running in the UML is spawnRunner
The RunnerFactory organizes lists of these clients and manages their states
There is one UserEditorsOnOneScraper per user per scraper to handle one user opening multiple windows onto the same scraper
There is one EditorsOnOneScraper per scraper which bundles logged in users into a list of UserEditorsOnOneScrapers

"""

import sys
import os
import signal
import time
from optparse import OptionParser
import ConfigParser
import datetime

varDir = './var'

try:    import json
except: import simplejson as json

from twisted.internet import protocol, utils, reactor, task

# for calling back to the scrapers/twister/status
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.internet.defer import succeed

agent = Agent(reactor)

def jstime(dt):
    return str(1000*int(time.mktime(dt.timetuple()))+dt.microsecond/1000)

class spawnRunner(protocol.ProcessProtocol):
    
    def __init__(self, client, code):
        self.client = client
        self.code = code
        self.runID = None
        self.umlname = ''
        self.buffer = ''
    
    def connectionMade(self):
        print "Starting run"
        self.transport.write(self.code)
        self.transport.closeStdin()
    
    # messages from the UML
    def outReceived(self, data):
        print "out", self.client.guid, data[:100]
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

    def processEnded(self, reason):
        self.client.processrunning = None
        self.client.writeall(json.dumps({'message_type':'executionstatus', 'content':'runfinished'}))
        self.client.factory.notifyMonitoringClients(self.client)
        if reason.type == 'twisted.internet.error.ProcessDone':
            print "run process ended ", reason
        else:
            print "run process ended ok"



# There's one of these 'clients' per editor window open.  All connecting to same factory
class RunnerProtocol(protocol.Protocol):  # Question: should this actually be a LineReceiver?

    def __init__(self):
        # Set if a run is currently taking place, to make sure we don't run 
        # more than one scraper at a time.
        self.processrunning = None
        self.guid = ""
        self.scrapername = ""
        self.isstaff = False
        self.username = ""
        self.userrealname = ""
        self.chatname = ""
        self.cchatname = ""            # combined real/chatname version delimited with | for sending to umlmonitor
        self.clientnumber = -1         # number for whole operation of twisted
        self.clientsessionbegan = datetime.datetime.now()
        self.clientlasttouch = self.clientsessionbegan
        self.guidclienteditors = None  # the EditorsOnOneScraper object
        self.automode = 'autosave'     # draft, autosave, autoload, autotype
        self.isumlmonitoring = None  # used to designate as not being initialized at all (bug if connection lost before it was successfully connected)

    def connectionMade(self):
        self.factory.clientConnectionMade(self)
            # we don't know what scraper they've opened until information is send with first clientcommmand
    
    # message from the clientclientsessionbegan via dataReceived
    def lconnectionopen(self, parsed_data):
        self.guid = parsed_data.get('guid', '')
        self.username = parsed_data.get('username', '')
        self.userrealname = parsed_data.get('userrealname', self.username)
        self.scrapername = parsed_data.get('scrapername', '')
        self.scraperlanguage = parsed_data.get('language', '')
        self.isstaff = (parsed_data.get('isstaff') == "yes")
        self.isumlmonitoring = (parsed_data.get('umlmonitoring') == "yes")
        
        if self.username:
            self.chatname = self.userrealname or self.username
        else:
            self.chatname = "Anonymous%d" % self.factory.anonymouscount
            self.factory.anonymouscount += 1
        self.cchatname = "%s|%s" % (self.username, self.chatname)
        self.factory.clientConnectionRegistered(self)  # this will cause a notifyEditorClients to be called for everyone on this scraper


    def connectionLost(self, reason):
        if self.processrunning:
            self.kill_run(reason='connection lost')
        self.factory.clientConnectionLost(self)

        
    # messages from the client
    def dataReceived(self, data):
        # chunking has recently become necessary because records (particularly from typing) can get concatenated
        # probably shows we should be using LineReceiver
        for lline in data.split("\r\n"):
            line = lline.strip()
            if line:
                try:
                    parsed_data = json.loads(line)
                except ValueError:
                    self.writejson({'content':"Command not json parsable:  %s " % line, 'message_type':'console'})
                    continue
                command = parsed_data.get('command')
                self.clientcommand(command, parsed_data)
        
            
    def clientcommand(self, command, parsed_data):
        
        # update the lasttouch values on associated aggregations
        if command != 'automode':
            self.clientlasttouch = datetime.datetime.now()
            if self.guid and self.automode != 'draft' and self.username:
                assert self.username in self.guidclienteditors.usereditormap
                self.guidclienteditors.usereditormap[self.username].userlasttouch = self.clientlasttouch
                self.guidclienteditors.scraperlasttouch = self.clientlasttouch

        # data uploaded when a new connection is made from the editor
        if command == 'connection_open':
            self.lconnectionopen(parsed_data)
            
        elif command == 'saved':
            line = json.dumps({'message_type' : "saved", 'chatname' : self.chatname})
            otherline = json.dumps({'message_type' : "othersaved", 'chatname' : self.chatname})
            self.writeall(line, otherline)
            self.factory.notifyMonitoringClientsSmallmessage(self, "savenote")


    # this signal needs to be more organized, esp to send out the the monitoring users to update the activity
    # and find a way for showing to watching users if anything at all is going on in the last hour
    # Long term inactivity will be the trigger that allows someone else to grab the editorship from another user.  
        elif command == 'typing':
            jline = {'message_type' : "typing", 'content' : "%s typing" % self.chatname}
            jotherline = {'message_type' : "othertyping", 'content' : "%s typing" % self.chatname}
            if "insertlinenumber" in parsed_data:
                jotherline["insertlinenumber"] = parsed_data["insertlinenumber"]
                jotherline["deletions"] = parsed_data["deletions"]
                jotherline["insertions"] = parsed_data["insertions"]
            self.writeall(json.dumps(jline), json.dumps(jotherline))
            self.factory.notifyMonitoringClientsSmallmessage(self, "typingnote")
            
        elif command == 'run':
            if self.processrunning:
                self.writejson({'content':"Already running! (shouldn't happen)", 'message_type':'console'}); 
                return 
            if self.username:
                if self.automode == 'autoload':
                    self.writejson({'content':"Not supposed to run! "+self.automode, 'message_type':'console'}); 
                    return 
            
            self.runcode(parsed_data)
        
        elif command == "kill":
            if self.processrunning:
                self.kill_run()
            elif self.username and self.guid:   # allows the killing of a process in another open window by same user
                usereditor = self.guidclienteditors.usereditormap[self.username]
                for client in usereditor.userclients:
                    if client.automode != 'draft' and client.processrunning:
                        client.kill_run()

        elif command == 'chat':
            line = json.dumps({'message_type':'chat', 'chatname':self.chatname, 'message':parsed_data.get('text'), 'nowtime':jstime(datetime.datetime.now()) })
            self.writeall(line)
        
        elif command == 'automode':
            automode = parsed_data.get('automode')
            if automode == self.automode:
                return
            
            if not self.username:
                self.automode = automode
                self.factory.notifyMonitoringClients(self)
                return

            usereditor = self.guidclienteditors.usereditormap[self.username]
            if automode == 'draft':
                usereditor.nondraftcount -= 1
                if self.processrunning:
                    self.kill_run(reason='convert to draft')
                
            elif self.automode == 'draft':  # change back from draft (can't happen for now)
                assert False
                usereditor.nondraftcount += 1

                # self-demote to autoload mode while choosing to promote a particular person to editing mode
            elif automode == 'autoload':
                selectednexteditor = parsed_data.get('selectednexteditor')
                if selectednexteditor and selectednexteditor in self.guidclienteditors.usereditormap:
                    assert self.guidclienteditors.usereditormap[selectednexteditor].usersessionpriority >= usereditor.usersessionpriority
                    self.guidclienteditors.usereditormap[selectednexteditor].usersessionpriority = usereditor.usersessionpriority
                usereditor.usersessionpriority = self.guidclienteditors.usersessionprioritynext
                self.guidclienteditors.usersessionprioritynext += 1
                selectednexteditor
            
                # another of the same users windows takes it out of autotype mode
            elif automode == 'autosave':
                for client in usereditor.userclients:
                    if client.automode == 'autotype':
                        client.automode = 'autosave'
            
            self.automode = automode
            assert usereditor.nondraftcount == len([lclient  for lclient in usereditor.userclients  if lclient.automode != 'draft'])
            
            self.guidclienteditors.notifyEditorClients("")
            self.factory.notifyMonitoringClients(self)

        # this message helps kill it better and killing it from the browser end
        elif command == 'loseconnection':
            self.transport.loseConnection()
    
    # message to the client
    def writeline(self, line):
        self.transport.write(line+",\r\n")  # note the comma added to the end for json parsing when strung together
    
    def writejson(self, data):
        self.writeline(json.dumps(data))
    

    def writeall(self, line, otherline=""):
        if line: 
            self.writeline(line)  
        
        if self.automode == 'draft':
            pass
        elif self.guidclienteditors:
            if not otherline:
                otherline = line
            
            for client in self.guidclienteditors.anonymouseditors:
                if client != self and client.automode != 'draft':
                    client.writeline(otherline); 
            
            for usereditor in self.guidclienteditors.usereditormap.values():
                for client in usereditor.userclients:
                    if client != self and client.automode != 'draft':
                        client.writeline(otherline); 
        else:
            assert not self.guid
            
            
    def kill_run(self, reason=''):
        msg = 'Script cancelled'
        if reason:
            msg = "%s (%s)" % (msg, reason)
        self.writeall(json.dumps({'message_type':'executionstatus', 'content':'killsignal', 'message':msg}))
        print msg
        try:      # (should kill using the new dispatcher call)
            os.kill(self.processrunning.pid, signal.SIGKILL)
        except:
            pass

    def runcode(self, parsed_data):
        
        code = parsed_data.get('code', '')
        code = code.encode('utf8')
        
        # these could all be fetched from self
        guid = parsed_data.get('guid', '')
        scraperlanguage = parsed_data.get('language', 'python')
        scrapername = parsed_data.get('scrapername', '')
        scraperlanguage = parsed_data.get('language', '')
        urlquery = parsed_data.get('urlquery', '')

        assert guid == self.guid
        args = ['./firestarter/runner.py']
        args.append('--guid=%s' % guid)
        args.append('--language=%s' % scraperlanguage)
        args.append('--name=%s' % scrapername)
        args.append('--urlquery=%s' % urlquery)
        args = [i.encode('utf8') for i in args]
        print "./firestarter/runner.py: %s" % args

        # from here we should somehow get the runid
        self.processrunning = reactor.spawnProcess(spawnRunner(self, code), './firestarter/runner.py', args, env={'PYTHON_EGG_CACHE' : '/tmp'})
        self.factory.notifyMonitoringClients(self)


        

class UserEditorsOnOneScraper:
    def __init__(self, client, lusersessionpriority):
        self.username = client.username 
        self.userclients = [ ]
        self.usersessionbegan = None
        self.usersessionpriority = lusersessionpriority  # list of users on a scraper sorted by this number, and first one in list gets the editorship
        self.nondraftcount = 0
                # need another value to mark which are the watchers and which are the editors (or derive this)
                # the states are enacted by the browser (by changing the dropdown or allowing user to change the drop down)
                # on the basis of the information supplied to it
        self.userlasttouch = datetime.datetime.now()
        self.AddUserClient(client)
    
    def AddUserClient(self, client):
        assert self.username == client.username
        if not self.userclients:
            assert not self.usersessionbegan
            self.usersessionbegan = client.clientsessionbegan
        if client.automode != 'draft':
            self.nondraftcount += 1
        self.userclients.append(client)
        assert self.nondraftcount == len([lclient  for lclient in self.userclients  if lclient.automode != 'draft'])
        
    def RemoveUserClient(self, client):
        assert self.username == client.username
        assert client in self.userclients
        self.userclients.remove(client)
        if client.automode != 'draft':
            self.nondraftcount -= 1
        assert self.nondraftcount == len([lclient  for lclient in self.userclients  if lclient.automode != 'draft'])
        return len(self.userclients)
        
        
class EditorsOnOneScraper:
    def __init__(self, guid, scrapername, scraperlanguage):
        self.guid = guid
        self.scrapername = scrapername
        self.scraperlanguage = scraperlanguage
        self.scrapersessionbegan = None
        self.anonymouseditors = [ ]
        self.scraperlasttouch = datetime.datetime.now()
        self.usereditormap = { }  # maps username to UserEditorsOnOneScraper
        self.usersessionprioritynext = 0
        
    def AddClient(self, client):
        assert client.guid == self.guid
        
        if not self.anonymouseditors and not self.usereditormap:
            assert not self.scrapersessionbegan
            self.scrapersessionbegan = client.clientsessionbegan

        if client.username:
            if client.username in self.usereditormap:
                self.usereditormap[client.username].AddUserClient(client)
            else:
                self.usereditormap[client.username] = UserEditorsOnOneScraper(client, self.usersessionprioritynext)
                self.usersessionprioritynext += 1
        else:
            self.anonymouseditors.append(client)
        
        client.guidclienteditors = self
        
    def RemoveClient(self, client):
        assert client.guid == self.guid
        assert client.guidclienteditors == self
        client.guidclienteditors = None
        
        if client.username:
            assert client.username in self.usereditormap
            if not self.usereditormap[client.username].RemoveUserClient(client):
                del self.usereditormap[client.username]
        else:
            assert client in self.anonymouseditors
            self.anonymouseditors.remove(client)
        return self.usereditormap or self.anonymouseditors
        
        
    def notifyEditorClients(self, message):
        editorstatusdata = { 'message_type':"editorstatus" }
        
        editorstatusdata["nowtime"] = jstime(datetime.datetime.now())
        editorstatusdata['earliesteditor'] = jstime(self.scrapersessionbegan)
        editorstatusdata["scraperlasttouch"] = jstime(self.scraperlasttouch)
        
                # order by who has first session (and not all draft mode) in order to determin who is the editor
        usereditors = [ usereditor  for usereditor in self.usereditormap.values()  if usereditor.nondraftcount ]
        usereditors.sort(key=lambda x: x.usersessionpriority)
        editorstatusdata["loggedineditors"] = [ usereditor.username  for usereditor in usereditors ]
        
        # notify if there is a broadcasting editor so the windows can sort out which one's are autoloading
        for usereditor in usereditors:
            for client in usereditor.userclients:
                if client.automode == 'autotype':
                    editorstatusdata["broadcastingeditor"] = usereditor.username
                    
        
        editorstatusdata["nanonymouseditors"] = len(self.anonymouseditors)
        editorstatusdata["message"] = message
        for client in self.anonymouseditors:
            editorstatusdata["chatname"] = client.chatname
            client.writejson(editorstatusdata); 
        
        for usereditor in self.usereditormap.values():
            for client in usereditor.userclients:
                editorstatusdata["chatname"] = client.chatname
                client.writejson(editorstatusdata) 
    
    def Dcountclients(self):
        return len(self.anonymouseditors) + sum([len(usereditor.userclients)  for usereditor in self.usereditormap.values()])


class RunnerFactory(protocol.ServerFactory):
    protocol = RunnerProtocol
    
    def __init__(self):
        self.clients = [ ]   # all clients
        self.clientcount = 0
        self.anonymouscount = 1
        self.announcecount = 0
        
        self.umlmonitoringclients = [ ]
        self.draftscraperclients = [ ]
        self.guidclientmap = { }  # maps to EditorsOnOneScraper objects
        
        # set the visible heartbeat goingthere
        #self.lc = task.LoopingCall(self.announce)
        #self.lc.start(10)

        self.m_conf        = ConfigParser.ConfigParser()
        config = '/var/www/scraperwiki/uml/uml.cfg'
        self.m_conf.readfp (open(config))
        self.twisterstatusurl = self.m_conf.get('twister', 'statusurl')
        

    # every 10 seconds sends out a quiet poll
    def announce(self):
        pass

        
    # throw in the kitchen sink to get the features.  optimize for changes later
    # should also allocate an automode (from among the windows that a scraper user has)
    def notifyMonitoringClients(self, cclient):  # cclient is the one whose state has changed (it can be normal editor or a umlmonitoring case)
        assert len(self.clients) == len(self.umlmonitoringclients) + len(self.draftscraperclients) + sum([eoos.Dcountclients()  for eoos in self.guidclientmap.values()])
        
        # both of these are in the same format and read the same, but changes are shorter
        umlstatuschanges = {'message_type':"umlchanges", "nowtime":jstime(datetime.datetime.now()) }; 
        if cclient.isumlmonitoring:
             umlstatusdata = {'message_type':"umlstatus", "nowtime":umlstatuschanges["nowtime"]}
        else:
             umlstatusdata = None
        
        # the cchatnames are username|chatname, so the javascript has something to handle for cases of "|Anonymous5" vs "username|username"
        
        # handle updates and changes in the set of clients that have the monitoring window open
        umlmonitoringusers = { }
        for client in self.umlmonitoringclients:
            if client.cchatname in umlmonitoringusers:
                umlmonitoringusers[client.cchatname] = max(client.clientlasttouch, umlmonitoringusers[client.cchatname])
            else:
                umlmonitoringusers[client.cchatname] = client.clientlasttouch
        #umlmonitoringusers = set([ client.cchatname  for client in self.umlmonitoringclients ])
        if umlstatusdata:
            umlstatusdata["umlmonitoringusers"] = [ {"chatname":chatname, "present":True, "lasttouch":jstime(chatnamelasttouch) }  for chatname, chatnamelasttouch in umlmonitoringusers.items() ]
        if cclient.isumlmonitoring:
            umlstatuschanges["umlmonitoringusers"] = [ {"chatname":cclient.cchatname, "present":(cclient.cchatname in umlmonitoringusers), "lasttouch":jstime(cclient.clientlasttouch) } ]
        
        # handle draft scraper users and the run states (one for each user, though there may be multiple draft scrapers for them)
        draftscraperusers = { }  # chatname -> running state
        for client in self.draftscraperclients:
            draftscraperusers[client.cchatname] = bool(client.processrunning) or draftscraperusers.get(client.cchatname, False)
        if umlstatusdata:
            umlstatusdata["draftscraperusers"] = [ {"chatname":chatname, "present":True, "running":crunning }  for chatname, crunning in draftscraperusers.items() ]
        if not cclient.isumlmonitoring and not cclient.guid:
            umlstatuschanges["draftscraperusers"] = [ { "chatname":cclient.cchatname, "present":(cclient.cchatname in draftscraperusers), "running":draftscraperusers.get(cclient.cchatname, False) } ]
        
        # the complexity here reflects the complexity of the structure.  the running flag could be set on any one of the clients
        def scraperentry(eoos, cclient):  # local function
            scrapereditors = { }   # chatname -> (lasttouch, nondraftcount)
            scraperdrafteditors = [ ]
            running = False        # we could make this an updated member of EditorsOnOneScraper like lasttouch
            
            for usereditor in eoos.usereditormap.values():
                if usereditor.nondraftcount != 0:
                    scrapereditors[usereditor.userclients[0].cchatname] = (usereditor.userlasttouch, usereditor.nondraftcount)
                else:
                    scraperdrafteditors.append(usereditor.userclients[0].cchatname)
                    
                for uclient in usereditor.userclients:
                    running = running or bool(uclient.processrunning)
            
            for uclient in eoos.anonymouseditors:
                if uclient.automode != 'draft': 
                    scrapereditors[uclient.cchatname] = (uclient.clientlasttouch, 1)
                else:
                    scraperdrafteditors.append(uclient.cchatname)
                running = running or bool(uclient.processrunning)
            
            ### scraperdrafteditors
            if cclient:
                scraperusercclient = {'chatname':cclient.cchatname, 'present':(cclient.cchatname in scrapereditors), 'userlasttouch':jstime(cclient.clientlasttouch) }
                if scraperusercclient['present']:
                    scraperusercclient['nondraftcount'] = (not cclient.username and 1 or eoos.usereditormap[cclient.username].nondraftcount)
                scraperusers = [ scraperusercclient ]
            else:
                scraperusers = [ {'chatname':cchatname, 'present':True, 'userlasttouch':jstime(ultc[0]), 'nondraftcount':ultc[1] }  for cchatname, ultc in scrapereditors.items() ]
            
            return {'scrapername':eoos.scrapername, 'present':True, 'running':running, 'scraperusers':scraperusers, 'scraperlasttouch':jstime(eoos.scraperlasttouch) }
        
        
        if umlstatusdata:
            umlstatusdata["scraperentries"] = [ ]
            for eoos in self.guidclientmap.values():
                umlstatusdata["scraperentries"].append(scraperentry(eoos, None))
                
        if cclient.guid:
            if cclient.guid in self.guidclientmap:
                umlstatuschanges["scraperentries"] = [ scraperentry(self.guidclientmap[cclient.guid], cclient) ]
            else:
                umlstatuschanges["scraperentries"] = [ { 'scrapername':cclient.scrapername, 'present':False, 'running':False, 'scraperusers':[ ] } ]
        
        # send the status to the target and updates to everyone else who is monitoring
        #print "\numlstatus", umlstatusdata
        
        # new monitoring client
        if cclient.isumlmonitoring:
            cclient.writejson(umlstatusdata) 
        
        # send only updates to current clients
        for client in self.umlmonitoringclients:
            if client != cclient:
                client.writejson(umlstatuschanges) 

    # just a signal sent for the latest event
    def notifyMonitoringClientsSmallmessage(self, cclient, smallmessage):
        if cclient.guid:
            umlsavenotification = {'message_type':smallmessage, "scrapername":cclient.scrapername, "cchatname":cclient.cchatname, "nowtime":jstime(datetime.datetime.now()) }
            for client in self.umlmonitoringclients:
                client.writejson(umlsavenotification) 
            

    def clientConnectionMade(self, client):
        assert client.isumlmonitoring == None
        client.clientnumber = self.clientcount
        self.clients.append(client)
        self.clientcount += 1
            # next function will be called when some actual data gets sent

    def clientConnectionRegistered(self, client):
        assert client.isumlmonitoring != None
        
        if client.isumlmonitoring:
            self.umlmonitoringclients.append(client)
            
        elif client.guid:
            if client.guid not in self.guidclientmap:
                self.guidclientmap[client.guid] = EditorsOnOneScraper(client.guid, client.scrapername, client.scraperlanguage)
            
            if client.username in self.guidclientmap[client.guid].usereditormap:
                message = "%s opens another window" % client.chatname
            else:
                message = "%s enters" % client.chatname
            
            self.guidclientmap[client.guid].AddClient(client)
            self.guidclientmap[client.guid].notifyEditorClients(message)

        
        else:   # draft scraper type (hardcode the output that would have gone with notifyEditorClients
            editorstatusdata = {'message_type':"editorstatus", "loggedineditors":[], "nanonymouseditors":1, "chatname":client.chatname, "message":"Draft scraper connection" }
            editorstatusdata["nowtime"] = jstime(datetime.datetime.now())
            editorstatusdata['earliesteditor'] = jstime(client.clientsessionbegan)
            editorstatusdata["scraperlasttouch"] = jstime(client.clientlasttouch)
            
            client.writejson(editorstatusdata); 
            self.draftscraperclients.append(client)
        
        
        # check that all clients are accounted for
        assert len(self.clients) == len(self.umlmonitoringclients) + len(self.draftscraperclients) + sum([eoos.Dcountclients()  for eoos in self.guidclientmap.values()])
        self.notifyMonitoringClients(client)
            
    
    def clientConnectionLost(self, client):
        self.clients.remove(client)  # main list
        
        if client.isumlmonitoring == None:
            pass  # didn't even get to connection open
        
        elif client.isumlmonitoring:
            self.umlmonitoringclients.remove(client)

        elif not client.guid:
            self.draftscraperclients.remove(client)
            
        elif (client.guid in self.guidclientmap):   
            if not self.guidclientmap[client.guid].RemoveClient(client):
                del self.guidclientmap[client.guid]
            else:
                if client.username in self.guidclientmap[client.guid].usereditormap:
                    message = "%s closes a window" % client.chatname
                else:
                    message = "%s leaves" % client.chatname
                self.guidclientmap[client.guid].notifyEditorClients(message)
        else:
            pass  # shouldn't happen
        
        # check that all clients are accounted for
        assert len(self.clients) == len(self.umlmonitoringclients) + len(self.draftscraperclients) + sum([eoos.Dcountclients()  for eoos in self.guidclientmap.values()])
        self.notifyMonitoringClients(client)






def execute (port) :
    runnerfactory = RunnerFactory()
    reactor.listenTCP(port, runnerfactory)
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
