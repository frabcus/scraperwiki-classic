# You can run this .tac file directly with:
#    twistd -ny datastore.tac

"""
This is the tac file for the datastore
"""

import os, sys
from twisted.application import service, internet
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
import twisted.manhole.telnet

from datastore import DatastoreFactory

print sys.argv

application = service.Application("datastore")
logfile = DailyLogFile("datastore.log", "/var/log/scraperwiki/")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

# attach the service to its parent application
service = service.MultiService()

f = DatastoreFactory()
dsf = internet.TCPServer(2112, f)
dsf.setServiceParent( service )

manhole = twisted.manhole.telnet.ShellFactory()
manhole.username = "boss"
manhole.password = "sekrit"
manhole.namespace['server'] = dsf
manhole.namespace['factory'] = f
msvc = internet.TCPServer(8007, manhole)
msvc.setServiceParent( service )

service.setServiceParent(application)
