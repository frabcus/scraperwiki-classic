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

dr_service1 = internet.TCPServer(9003, DatarouterFactory(via_proxy=False))
dr_service1.setServiceParent( service )
dr_service2 = internet.TCPServer(80, DatarouterFactory(via_proxy=True))
dr_service2.setServiceParent( service )


service.setServiceParent(application)
