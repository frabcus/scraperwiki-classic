[dispatcher]
host	= 89.16.177.212
port	= 9000
umllist	= uml001,uml002,uml003,uml004
confurl	= http://localhost:8080/whitelist/config
path	= /scraperwiki/live/scrapers,/scraperwiki/live/scraperlibs

[twister]
statusurl = http://localhost:8080/scrapers/twister/status

[webproxy]
host	= 89.16.177.195
port	= 9002
dbhost	= 89.16.177.176
user	= cache
passwd	= 4dlk4eaaA44A1gTx
db	= swcache_live

[httpproxy]
host	= 89.16.177.195
port	= 9005
cache   = 127.0.0.1:11211

[httpsproxy]
host	= 89.16.177.195
port	= 9006
cache   = 127.0.0.1:11211

[ftpproxy]
host	= 89.16.177.195
port	= 9004

[dataproxy]
dbtype  = mysql
host    = 89.16.177.176
port    = 9003
user    = datastore
passwd  = 3jFjLrje6dFJ7cQE
db      = datastore_live
secure  = 89.16.177.212
resourcedir = /var/www/scraperwiki/resourcedir
max_api_distance = 10

[uml001]
host = 89.16.177.195
tap	= 192.168.254.101
eth	= 192.168.254.1
port = 9001
via	= 9101
mem	= 1024M
count = 25

[uml002]
host = 89.16.177.195
tap	= 192.168.254.102
eth	= 192.168.254.2
port = 9001
via	= 9102
mem	= 1024M
count = 25

[uml003]
host = 89.16.177.195
tap	= 192.168.254.103
eth	= 192.168.254.3
port = 9001
via	= 9103
mem	= 1024M
count = 25

[uml004]
host = 89.16.177.195
tap	= 192.168.254.104
eth	= 192.168.254.4
port = 9001
via	= 9104
mem	= 1024M
count = 25

[uml005]
host = 89.16.177.176
tap	= 192.168.254.101
eth	= 192.168.254.1
port = 9001
via	= 9101
mem	= 1024M
count = 25

[uml006]
host = 89.16.177.176
tap	= 192.168.254.102
eth	= 192.168.254.2
port = 9001
via	= 9102
mem	= 1024M
count = 25

[uml007]
host = 89.16.177.176
tap	= 192.168.254.103
eth	= 192.168.254.3
port = 9001
via	= 9103
mem	= 1024M
count = 25

[uml008]
host = 89.16.177.176
tap	= 192.168.254.104
eth	= 192.168.254.4
port = 9001
via	= 9104
mem	= 1024M
count = 25

[loggers]
keys=root,dataproxy,controller

[handlers]
keys=consoleHandler,logfileHandlerDataproxyDebug,logfileHandlerDataproxyWarning,logfileHandlerDataproxyEmail,logfileHandlerControllerDebug,logfileHandlerControllerWarning

[formatters]
keys=simpleFormatter


[logger_root]
level=CRITICAL
handlers=consoleHandler

[logger_dataproxy]
level=DEBUG
handlers=logfileHandlerDataproxyDebug,logfileHandlerDataproxyWarning
qualname=dataproxy
propagate=0

[logger_controller]
level=DEBUG
handlers=logfileHandlerControllerDebug,logfileHandlerControllerWarning
qualname=controller
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)


[handler_logfileHandlerControllerDebug]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/controller.log', "a", 100000, 5)

[handler_logfileHandlerControllerWarning]
class=handlers.RotatingFileHandler
level=WARNING
formatter=simpleFormatter
args=('/var/log/scraperwiki/controller.log-warn', "a", 100000, 5)



[handler_logfileHandlerDataproxyDebug]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('/var/log/scraperwiki/dataproxy.log', "a", 100000, 5)

[handler_logfileHandlerDataproxyWarning]
class=handlers.RotatingFileHandler
level=WARNING
formatter=simpleFormatter
args=('/var/log/scraperwiki/dataproxy.log-warn', "a", 100000, 5)

[handler_logfileHandlerDataproxyEmail]
class=handlers.SMTPHandler
level=CRITICAL
formatter=simpleFormatter
args=(('localhost', 25,), 'server@scraperwiki.com', ['julian@scraperwiki.com'], 'ScraperWiki error in dataproxy')



[formatter_simpleFormatter]
format=%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s

