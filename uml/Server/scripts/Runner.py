#!/usr/bin/python
import sys
import os
import time
import signal
import fcntl
import select
import cgi
import string
from optparse import OptionParser


try:
    import simplejson as json
except:
    import json

try: 
    import runner_config
except:
    print "Error: You need to set up runner_config before you can use runner."
    sys.exit()


sys.path.append	(runner_config.scripts_path)


# Make sure stdout doesn't buffer anything
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 10000000)

import FireStarter


def execute (code, guid = None) :

    def format_json(line):
        if line.startswith('<scraperwiki:message type="data">'):
            offset_len = len('<scraperwiki:message type="data">')
            message = {}
            message['content'] = json.loads(line[offset_len:])
            message['message_type'] = "data"
        
        elif line.startswith('<scraperwiki:message type="sources">'):
            offset_len = len('<scraperwiki:message type="sources">')
            message = json.loads(line[offset_len:])
            message['message_type'] = "sources"

        elif line.startswith('<scraperwiki:message type="exception">'):
            offset_len = len('<scraperwiki:message type="exception">')
            message = json.loads(line[offset_len:])
            message['message_type'] = "exception"
            message['content'] = cgi.escape(message['content'])
            message['content_long'] = cgi.escape(message['content_long'])

        elif line.startswith('<scraperwiki:message type="fail">'):
            offset_len = len('<scraperwiki:message type="fail">')
            message = json.loads(line[offset_len:])
            message['message_type'] = "fail"
            message['content'] = cgi.escape(message['content'])

        else :
            offset_len = len('<scraperwiki:message type="console">')
            message = json.loads(line[offset_len:])
            message['message_type'] = "console"
            message['content'] = cgi.escape(message['content'])
            try :
                message['content_long'] = cgi.escape(message['content_long'])
            except :
                pass

        return json.dumps(message)

    fs  = FireStarter.FireStarter()    
    
    fs.setTestName     ('Runner')
    fs.setScraperID    (guid)
    
    fs = runner_config.config(fs)
    
    res = fs.execute (string.replace (code, '\r', ''), True)
    if res is None :
        print format_json('<scraperwiki:message type="fail">%s' % json.dumps({ 'content' : fs.error() }))
        return

    line = res.readline()
    while line != '' and line is not None :
        print format_json(line), "\r\n"
        sys.stdout.flush()
        line = res.readline()



if __name__ == "__main__":
    
    
    parser = OptionParser()
    parser.add_option("-g", "--guid", dest="guid", action="store", type='str',
                      help="GUID of the scraper",  
                      default=None, metavar="GUID")

    (options, args) = parser.parse_args()

    guid = options.guid
    code = sys.stdin.read()

    execute (code, guid)

