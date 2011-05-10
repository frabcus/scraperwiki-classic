#!/usr/bin/python -W ignore::DeprecationWarning

import  sys
import  os
import  socket
import  signal
import  string
import  time
import  urllib2
import optparse

try    : import json
except : import simplejson as json

class ConsoleStream:
    def __init__(self, fd):
        self.m_text = ''
        self.m_fd = fd

    def saveunicode(self, text):
        try:    return unicode(text)
        except UnicodeDecodeError:     pass
        try:    return unicode(text, encoding='utf8')
        except UnicodeDecodeError:     pass
        try:    return unicode(text, encoding='latin1')
        except UnicodeDecodeError:     pass
        return unicode(text, errors='replace')
    
    def write(self, text):
        self.m_text += self.saveunicode(text)
        if self.m_text and self.m_text[-1] == '\n' :
            self.flush()

    def flush(self) :
        if self.m_text:
            scraperwiki.dumpMessage({'message_type': 'console', 'content': self.m_text})
            self.m_text = ''

    def close(self):
        self.m_fd.close()

    def fileno(self):
        return self.m_fd.fileno()

parser = optparse.OptionParser()
parser.add_option("--script", metavar="name")
parser.add_option("--path", metavar="path")
parser.add_option("--http", metavar="proxy")
parser.add_option("--https", metavar="proxy")
parser.add_option("--ftp", metavar="proxy")
parser.add_option("--ds", metavar="server:port")
parser.add_option("--uid")
parser.add_option("--gid")
options, args = parser.parse_args()

if options.uid is not None :
    os.setreuid(int(options.uid), int(options.uid))
if options.gid is not None :
    os.setregid(int(options.gid), int(options.gid))

if options.path is not None :
    for p in string.split (options.path, ':') :
        sys.path.append(p)


#  Imports cannot be done until sys.path is set
import  scraperwiki

scraperwiki.logfd = os.fdopen(3, 'w', 0)
sys.stdout = ConsoleStream(scraperwiki.logfd)
sys.stderr = ConsoleStream(scraperwiki.logfd)


#  These seem to be needed for urllib.urlopen() to support proxying, though
#  FTP doesn't actually work.
#

# uncomment the following line and the ProxyHandler lines if you want proxying to work 
# in a local version

        # This is not used in the real deployed version as it uses another lower level method within the UMLs
        # ... although it does not appear to have been built for ftp (so you might not get ftp for PHP version)
##os.environ['http_proxy' ] = options.http
##os.environ['https_proxy'] = options.https
os.environ['ftp_proxy'  ] = options.ftp
scraperwiki.utils.urllibSetup   ()

#  This is for urllib2.urlopen() (and hence scraperwiki.scrape()) where
#  we can set explicit handlers.
#
scraperwiki.utils.urllib2Setup \
    (
##        urllib2.ProxyHandler ({'http':  options.http }),
##        urllib2.ProxyHandler ({'https': options.https}),
        urllib2.ProxyHandler ({'ftp':   options.ftp  })
    )


host, port = string.split(options.ds, ':')
scraperwiki.datastore.create(host, port)



#  Set up a CPU time limit handler which simply throws a python
#  exception.
#
# (technical question: what happens if the user script traps this exception and ignores it? --JGT)
# (answer: it will be brutally killed when the hard CPU time limit is reached.
# See "man setrlimit", "If the process continues to consume CPU time, it will
# be sent  SIGXCPU once per second until the hard limit is reached, at which
# time it is sent SIGKILL". This is one second later, as the runner does
# "fs.setCPULimit      (cpulimit, cpulimit+1)". --FAI)
def sigXCPU (signum, frame) :
    raise Exception ("ScraperWiki CPU time exceeded")
signal.signal (signal.SIGXCPU, sigXCPU)


code = open(options.script).read()
try :
    import imp
    mod        = imp.new_module ('scraper')
    exec code.rstrip() + "\n" in mod.__dict__

except Exception, e :
    etb = scraperwiki.stacktrace.getExceptionTraceback(code)  
    assert etb.get('message_type') == 'exception'
    scraperwiki.dumpMessage(etb)


# force ConsoleStream to output last line, even if no \n
sys.stdout.flush()
sys.stderr.flush()
