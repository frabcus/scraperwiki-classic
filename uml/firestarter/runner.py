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


def execute (code, options) :

    fs  = firestarter.FireStarter('/var/www/scraperwiki/uml/uml.cfg')
    cpulimit = int(options.cpulimit)
    
    fs.setUser          ('nobody' )
    fs.setGroup         ('nogroup')

    fs.setCPULimit      (cpulimit, cpulimit+1)
    fs.setDraft         (options.draft    )

    fs.loadConfiguration()

    jdata = {'language':options.language, "scraperid":options.guid, "urlquery":options.urlquery, "scrapername":options.name, "scraperid":options.guid }
    jdata["code"] = string.replace (code, '\r', '')
    
    for message in fs.execute(jdata):
        sys.stdout.write(message + '\r\n')
        sys.stdout.flush()

#  You can test this script by typing:
#       echo "print 1" | python runner.py
#
if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("--guid")
    parser.add_option("--language", default='python')
    parser.add_option("--name", default='', metavar="SCRAPER_NAME")
    parser.add_option("--cpulimit", default='80')
    parser.add_option("--urlquery", default='')
    parser.add_option("--draft", action="store_true", default=False)

    options, args = parser.parse_args()
    code = sys.stdin.read()
    execute(code, options)
