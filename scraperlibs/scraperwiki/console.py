import  sys
import base64

try:     import json
except:  import simplejson as json


logfd = sys.stderr

def dumpMessage (d) :
    logfd.write (json.dumps (d))
    logfd.write ('\n')
    logfd.flush()

def logScrapedURL (url, length):
    dumpMessage ({'message_type':'sources', 'url':url, 'content': "%d bytes from %s" % (length, url)})

def logScrapedData(pdata) :
    dumpMessage ({'message_type':'data', 'content': pdata})

def logSqliteCall(command, val1, lval2) :
    dumpMessage ({'message_type':'sqlitecall', 'command': command, "val1":val1, "lval2":lval2})

def logMessage (message) :
    dumpMessage ({'message_type': 'console', 'content': message})

def logBinaryMessage (message) :
    dumpMessage ({'message_type':'console', 'content': base64.encodestring(message), 'encoding':"base64"})

def logHTTPResponseHeader (headerkey, headervalue) :
    dumpMessage ({'message_type': 'httpresponseheader', 'headerkey': headerkey, 'headervalue': headervalue})

def logWarning (message) :
    # could go out with a warning signal like an exception message in bold
    dumpMessage ({'message_type': 'console', 'content': 'Warning: ' + message})



class ConsoleStream:
    
    def __init__ (self, fd):
        self.m_text = ''
        self.m_fd = fd

    # Do our best to turn anything into unicode, for display on console
    # (for datastore, we give errors if it isn't already UTF-8)
    # XXX this is copied in controller for PHP, not sure how to share as
    # one is in sandbox one outside.
    def saveunicode(self, text):
        try:
            return unicode(text)
        except UnicodeDecodeError:
            pass
        
        try:
            return unicode(text, encoding='utf8')
        except UnicodeDecodeError:
            pass
    
        try:
            return unicode(text, encoding='latin1')
        except UnicodeDecodeError:
            pass
        
        return unicode(text, errors='replace')
    
    def write (self, text):
        self.m_text += self.saveunicode(text)
        if self.m_text and self.m_text[-1] == '\n' :
            self.flush ()

    def flush (self) :
        if self.m_text:
            logMessage(self.m_text)
            self.m_text = ''

    def close (self):
        self.m_fd.close()

    def fileno (self):
        return self.m_fd.fileno()

