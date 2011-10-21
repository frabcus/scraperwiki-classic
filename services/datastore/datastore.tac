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
from datarouter import DatarouterFactory

application = service.Application("datastore")
logfile = DailyLogFile("datastore.log", "/var/log/scraperwiki/")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

# attach the service to its parent application
service = service.MultiService()


# Setup the datastore servers - on ports from >10000
# One per CPU and then ...
ds_factory = DatastoreFactory()
ds_service = internet.TCPServer(9003, ds_factory)
ds_service.setServiceParent( service )

# Setup the datarouter on 9003 and tell it where the 
# stores are....
dr_factory = DatastoreFactory()

# Instances should be tuples of (host,port)
dr_factory.set_instances([])
dr_service = internet.TCPServer(1000, dr_factory)
dr_service.setServiceParent( service )


# Setup manhole, although it appears we can't quit and instead
# have to CTRL+] instead.
manhole = twisted.manhole.telnet.ShellFactory()
manhole.username = "boss"
manhole.password = "sekrit"
manhole.namespace['server'] = dsf
manhole.namespace['factory'] = f
msvc = internet.TCPServer(8007, manhole)
msvc.setServiceParent( service )

service.setServiceParent(application)
