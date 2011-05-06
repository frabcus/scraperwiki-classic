import  settings
import  socket
import  urllib

try:
    import json
except: 
    import simplejson as json


class DataStore(object):

    def __init__ (self, scraperID, short_name) :
        self.m_socket   = None
        self.m_host     = settings.DATAPROXY_HOST
        self.m_port     = settings.DATAPROXY_PORT

        self.connect (scraperID, short_name)
        self.sbuffer = [ ] 

    def connect (self, scraperID, short_name) :
        assert not self.m_socket
        self.m_socket    = socket.socket()
        self.m_socket.connect ((self.m_host, self.m_port))
        data = [ ("uml", socket.gethostname()), ("port", self.m_socket.getsockname()[1]), ("scraperid", scraperID), ("short_name", short_name) ]
        self.m_socket.send ('GET /?%s HTTP/1.1\n\n' % urllib.urlencode(data))
        
        res = self.receiveoneline()  # comes back with True, "Ok"
        assert res.get("status") == "good", res
        

    def request(self, req) :
        self.m_socket.sendall(json.dumps(req) + '\n')
        return self.receiveoneline()

    def close(self) :
        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None

    
    # a \n delimits the end of the record.  you cannot read beyond it or it will hang; unless there is a moredata=True parameter
    def receiveonelinenj(self):
        while len(self.sbuffer) >= 2:
            res = self.sbuffer.pop(0)
            if res:
                return res
        while True:
            srec = self.m_socket.recv(1024)
            if not srec:
                return json.dumps({'error': "socket from dataproxy has unfortunately closed"})
            ssrec = srec.split("\n")  # multiple strings if a "\n" exists
            self.sbuffer.append(ssrec.pop(0))
            if ssrec:
                break # Discard anything after the newline
        
        line = "".join(self.sbuffer)
        self.sbuffer = ssrec
        return line
        
        
    def receiveoneline(self):
        self.sbuffer = [ ] # reset the buffer just for sake of that's what's worked in the past
        try:
            ret = json.loads(self.receiveonelinenj())
        except ValueError, e:
            raise Exception("%s:%s" % (e.message, text))
        assert "moredata" not in ret
        return ret
    