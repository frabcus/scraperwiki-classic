#!/usr/bin/env python
import sys
import os
import time
import signal
import fcntl
import select
import cgi
import string
from   optparse import OptionParser


try:
    import simplejson as json
except:
    import json

# Make sure stdout doesn't buffer anything
#
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 10000000)

import firestarter


def execute (code, guid = None, language = None) :

    def format_json(line):
        message = json.loads(line)
        for key in [ 'content', 'content_long' ] :
            try    : message[key] = cgi.escape(message[key])
            except : pass
        return json.dumps(message)

    fs  = firestarter.FireStarter('/var/www/scraperwiki/uml/uml.cfg')
    
    fs.setTestName      ('Runner' )
    fs.setScraperID     (guid     )
    fs.setLanguage      (language )
    fs.setUser          ('nobody' )
    fs.setGroup         ('nogroup')

    fs.setTraceback     ('text')
    fs.addPaths         ('/scraperwiki/live/scrapers')
    fs.addPaths         ('/scraperwiki/live/scraperlibs')
    fs.setCache         (3600 * 12)
    fs.setCPULimit      (80, 81)

    fs.loadConfiguration()

    code = string.replace (code, '\r', '')
    if language == "php" :
        code = "<?php\n%s\n?>\n" % code
    open("/tmp/args", "w").write("%s\n" % sys.argv)
    open("/tmp/code", "w").write("[%s]:%s\n" % (language, code))
    res = fs.execute (code, True)
    if res is None :
        sys.stdout.write (json.dumps({ 'message_type' : 'fail', 'content' : fs.error() }) + '\r\n')
        sys.stdout.flush ()
        return

    line = res.readline()
    while line != '' and line is not None :
        sys.stdout.write (format_json(line) + "\r\n")
        sys.stdout.flush ()
        line = res.readline()


# You can test this script by typing:
# echo "print 1" | python runner.py

if __name__ == "__main__":
    
    
    parser = OptionParser()

    parser.add_option \
        (   "-g",
            "--guid",
            dest    = "guid",
            action  = "store",
            type    = "str",
            help    = "GUID of the scraper",  
            default = None,
            metavar = "GUID"
        )

    parser.add_option \
        (   "-l",
            "--language",
            dest    = "language",
            action  = "store",
            type    = 'str',
            help    = "Programming language of the scraper",  
            default = 'python',
            metavar = "LANGUAGE"
        )
    
    parser.add_option \
        (   "-n",
            "--name",
            dest    = "name",
            action  = "store",
            type    = 'str',
            help    = "Short name of the scraper",  
            default = '',
            metavar = "NAME"
        )
    
    (options, args) = parser.parse_args()
    code = sys.stdin.read()
    execute (code, options.guid, options.language)
