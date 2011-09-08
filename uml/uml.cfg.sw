[dispatcher]
host    = 89.16.177.212
port    = 9000
umllist = uml001,uml002,uml003,uml004
confurl = http://localhost:8080/whitelist/config
path    = /scraperwiki/live/scrapers,/scraperwiki/live/scraperlibs

[twister]
statusurl = http://localhost:8080/scrapers/twister/status
port      = 9010
djangokey = jshdowpabzsdofosiw976gbjksjdbfslkaoapwebnvdjflg

[webproxy]
host    = 46.43.55.84
port    = 9002

[httpproxy]
host    = 46.43.55.84
port    = 9005
cache   = 127.0.0.1:11211

[httpsproxy]
host    = 46.43.55.84
port    = 9006
cache   = 127.0.0.1:11211

[ftpproxy]
host    = 46.43.55.84
port    = 9004

[dataproxy]
dbtype  = mysql
host    = 46.43.55.84
port    = 9003
user    = datastore
passwd  = 
db      = datastore_live
secure  = 89.16.177.212
resourcedir = /var/www/scraperwiki/resourcedir
max_api_distance = 10


[uml001]
host    = 46.43.55.84
tap = 192.168.254.101
eth = 192.168.254.1
port    = 9001
via = 9101
mem = 1024M
count   = 25



[uml002]
host    = 46.43.55.84
tap = 192.168.254.102
eth = 192.168.254.2
port    = 9001
via = 9102
mem = 1024M
count   = 25



[uml003]
host    = 46.43.55.84
tap = 192.168.254.103
eth = 192.168.254.3
port    = 9001
via = 9103
mem = 1024M
count   = 25



[uml004]
host    = 46.43.55.84
tap = 192.168.254.104
eth = 192.168.254.4
port    = 9001
via = 9104
mem = 1024M
count   = 25


[loggers]
keys=root,dataproxy,controller,runner,dispatcher,twister,proxy

[handlers]
keys=consoleHandler,logfileHandlerWarnings,logfileHandlerEmail,logfileHandlerDataproxyDebug,logfileHandlerControllerDebug,logfileHandlerDispatcherDebug,logfileHandlerRunnerDebug,logfileHandlerTwisterDebug,logfileHandlerProxyDebug

[formatters]
keys=simpleFormatter


[logger_root]
level=ERROR
handlers=consoleHandler

[logger_dataproxy]
level=DEBUG
handlers=logfileHandlerDataproxyDebug,logfileHandlerWarnings
qualname=dataproxy
propagate=0

[logger_controller]
level=DEBUG
handlers=logfileHandlerControllerDebug,logfileHandlerWarnings
qualname=controller
propagate=0

[logger_runner]
level=DEBUG
handlers=logfileHandlerRunnerDebug,logfileHandlerWarnings
qualname=runner
propagate=0

[logger_dispatcher]
level=DEBUG
handlers=logfileHandlerDispatcherDebug,logfileHandlerWarnings
qualname=dispatcher
propagate=0

[logger_twister]
level=DEBUG
handlers=logfileHandlerTwisterDebug,logfileHandlerWarnings
qualname=twister
propagate=0

[logger_proxy]
level=DEBUG
handlers=logfileHandlerProxyDebug,logfileHandlerWarnings
qualname=proxy
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[handler_logfileHandlerWarnings]
class=handlers.ConcurrentRotatingFileHandler
level=WARNING
formatter=simpleFormatter
args=('/var/log/scraperwiki/allwarnings.log', "a", 1000000000, 5)

[handler_logfileHandlerEmail]
class=handlers.SMTPHandler
level=CRITICAL
formatter=simpleFormatter
args=(('localhost', 25,), 'server@scraperwiki.com', ['julian@scraperwiki.com'], 'ScraperWiki critical error in system')


[handler_logfileHandlerControllerDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/controller.log', "a", 1000000000, 5)

[handler_logfileHandlerDataproxyDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/dataproxy.log', "a", 1000000000, 5)

[handler_logfileHandlerDispatcherDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/dispatcher.log', "a", 1000000000, 5)

[handler_logfileHandlerRunnerDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/runner.log', "a", 1000000000, 5)

[handler_logfileHandlerTwisterDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/twister.log', "a", 1000000000, 5)

[handler_logfileHandlerProxyDebug]
class=handlers.ConcurrentRotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/proxy.log', "a", 1000000000, 5)

[formatter_simpleFormatter]
format=%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s


