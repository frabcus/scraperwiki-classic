#!/usr/bin/env python
import sys
import os
import optparse


try:    import simplejson as json
except: import json

# Make sure stdout doesn't buffer anything
#
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 10000000)

import firestarter

def execute (code, options) :
    fs  = firestarter.FireStarter('/var/www/scraperwiki/uml/uml.cfg')
    jdata = {'language':options.language, "scraperid":options.guid, "urlquery":options.urlquery, "scrapername":options.name, 
             "scraperid":options.guid, "draft":options.draft, "user":"nobody", "group":"nogroup" }
    jdata["code"] = code.replace('\r', '')
    jdata["cpulimit"] = int(options.cpulimit)
    
    for message in fs.execute(jdata):
        sys.stdout.write(message + '\r\n')
        sys.stdout.flush()

#  You can test this script by typing:
#       echo "print 1" | python runner.py
#
if __name__ == "__main__":
    parser = optparse.OptionParser()

    parser.add_option("--guid")
    parser.add_option("--language", default='python')
    parser.add_option("--name", default='', metavar="SCRAPER_NAME")
    parser.add_option("--cpulimit", default='80')
    parser.add_option("--urlquery", default='')
    parser.add_option("--draft", action="store_true", default=False)

    options, args = parser.parse_args()
    code = sys.stdin.read()
    execute(code, options)
