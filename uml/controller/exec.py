#!/usr/bin/python -W ignore::DeprecationWarning

import  sys
import  os
import  socket
import  signal
import  string
import  time
import  urllib2, urllib
import  optparse
import  scraperwiki


try    : import json
except : import simplejson as json

    # Unfortunately necessary to do this because PYTHONUNBUFFERED=True does nto get good enough results and tends to still concatenate lines when short and rapid
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
parser.add_option("--script", metavar="name")    # not the scraper name, this is tmp file name which we load and execute
parser.add_option("--ds", metavar="server:port")
parser.add_option("--gid")    # nogroup
parser.add_option("--uid")    # nobody
parser.add_option("--scrapername")
parser.add_option("--runid")
options, args = parser.parse_args()

if options.gid:
    os.setregid(int(options.gid), int(options.gid))
if options.uid:
    os.setreuid(int(options.uid), int(options.uid))

scraperwiki.logfd = os.fdopen(3, 'w', 0)

host, port = string.split(options.ds, ':')
scraperwiki.datastore.create(host, port, options.scrapername, options.runid)

sys.stdout = ConsoleStream(scraperwiki.logfd)
sys.stderr = ConsoleStream(scraperwiki.logfd)

#  Set up a CPU time limit handler which simply throws a python so it can be handled cleanly before the hard limit is reached
def sigXCPU(signum, frame) :
    raise Exception("ScraperWiki CPU time exceeded")
signal.signal(signal.SIGXCPU, sigXCPU)

code = open(options.script).read()
try:
    import imp
    mod = imp.new_module('scraper')
    exec code.rstrip() + "\n" in mod.__dict__

except Exception, e:
    etb = scraperwiki.stacktrace.getExceptionTraceback(code)  
    assert etb.get('message_type') == 'exception'
    scraperwiki.dumpMessage(etb)


sys.stdout.flush()
sys.stderr.flush()