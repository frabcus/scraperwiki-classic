# You can run this .tac file directly with:
#    twistd -ny datarouter.tac

"""
This is the tac file for the datarouter
"""

import os, sys

from twisted.application import service, internet
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile

from datastore import DatastoreFactory
from datarouter import DatarouterFactory

application = service.Application("datarouter")
logfile = DailyLogFile("datarouter.log", "/var/log/scraperwiki/")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

# attach the service to its parent application
service = service.MultiService()

dr_factory = DatarouterFactory()
dr_service = internet.TCPServer(9003, dr_factory)
dr_service.setServiceParent( service )


service.setServiceParent(application)
