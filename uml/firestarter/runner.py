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
    
    fs.setTestName      (options.name     )
    fs.setScraperID     (options.guid     )
    fs.setLanguage      (options.language )
    fs.setUrlquery      (options.urlquery )
    fs.setUser          ('nobody' )
    fs.setGroup         ('nogroup')

    fs.setCPULimit      (cpulimit, cpulimit+1)
    fs.setDraft         (options.draft    )

    fs.loadConfiguration()

    code = string.replace (code, '\r', '')
    
    for message in fs.execute(code):
        sys.stdout.write(message + '\r\n')
        sys.stdout.flush()

#  You can test this script by typing:
#       echo "print 1" | python runner.py
#
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
    
    parser.add_option \
        (   "-c",
            "--cpulimit",
            dest    = "cpulimit",
            action  = "store",
            type    = 'str',
            help    = "Time limit for running script",  
            default = '80',
            metavar = "CPULIMIT"
        )
    
    parser.add_option \
        (   "-u",
            "--urlquery",
            dest    = "urlquery",
            action  = "store",
            type    = 'str',
            help    = "URL query argumentspassed in for a view",  
            default = '',
            metavar = "URLQUERY"
        )
    
    parser.add_option \
        (   "-d",
            "--draft",
            dest    = "draft",
            action  = "store_true",
            help    = "Run the scraper in draft mode not altering the database",  
            default = False,
        )
    
    (options, args) = parser.parse_args()
    code = sys.stdin.read()
    execute (code, options)
