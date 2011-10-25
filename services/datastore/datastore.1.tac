# You can run this .tac file directly with:
#    twistd -ny datastore.tac

"""
This is the tac file for the datastore
"""
from twisted.application import service, internet
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile

from datastore import DatastoreFactory
from datarouter import DatarouterFactory

application = service.Application("datastore_one")
logfile = DailyLogFile("datastore1.log", "/var/log/scraperwiki/")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

# attach the service to its parent application
service = service.MultiService()

port = 10000
ds_factory = DatastoreFactory()
ds_service = internet.TCPServer(port, ds_factory)
ds_service.setServiceParent( service )


service.setServiceParent(application)
