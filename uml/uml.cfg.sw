[dispatcher]
host	= 89.16.177.212
port	= 9000
umllist	= uml001,uml002,uml003,uml004

[httpproxy]
host	= 89.16.177.195
port	= 9002

[ftpproxy]
host	= 89.16.177.195
port	= 9004

[dataproxy]
dbtype	= mysql
host	= 89.16.177.176
port	= 9003
user	= user
passwd	= passwd
db	= datastore

[swlogger]
host    = 89.16.177.176
user    = scraperlog
passwd  = scr4p3rl0g
db      = swlog_live

[uml001]
host	= 89.16.177.195
tap	= 192.168.254.101
eth	= 192.168.254.1
port	= 9001
via	= 9101
mem	= 1024M
count	= 25

[uml002]
host	= 89.16.177.195
tap	= 192.168.254.102
eth	= 192.168.254.2
port	= 9001
via	= 9102
mem	= 1024M
count	= 25

[uml003]
host	= 89.16.177.195
tap	= 192.168.254.103
eth	= 192.168.254.3
port	= 9001
via	= 9103
mem	= 1024M
count	= 25

[uml004]
host	= 89.16.177.195
tap	= 192.168.254.104
eth	= 192.168.254.4
port	= 9001
via	= 9104
mem	= 1024M
count	= 25
