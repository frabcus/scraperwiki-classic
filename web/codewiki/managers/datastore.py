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

    def connect (self, scraperID, short_name) :

        """
        Connect to the data proxy.
        """
        assert not self.m_socket
        self.m_socket    = socket.socket()
        self.m_socket.connect ((self.m_host, self.m_port))
        data = [ ("uml", socket.gethostname()), ("port", self.m_socket.getsockname()[1]), ("scraperid", scraperID), ("short_name", short_name) ]
        self.m_socket.send ('GET /?%s HTTP/1.1\n\n' % urllib.urlencode(data))
        
        rc, arg = self.receiveoneline()  # comes back with True, "Ok"
        assert rc, arg
        

    def request(self, req) :
        self.m_socket.sendall(json.dumps(req) + '\n')
        return self.receiveoneline()


    def data_dictlist (self, tablename = "", limit = 1000, offset = 0, start_date = None, end_date = None, latlng = None) :
        
        if start_date is not None : start_date = str(start_date)
        if end_date   is not None : end_date   = str(  end_date)
        if latlng     is not None : latlng     = '%010.6f,%010.6f' % tuple(latlng)

        return self.request (('data_dictlist', tablename, limit, offset, start_date, end_date, latlng))


    def close(self) :
        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None

    
    # a \n delimits the end of the record.  you cannot read beyond it or it will hang; unless there is a moredata parameter
    def receiveonelinenj(self):
        sbuffer = [ ]
        while True:
            srec = self.m_socket.recv(1024)
            if not srec:
                return {'error': "socket from dataproxy has unfortunately closed"}
            ssrec = srec.split("\n")  # multiple strings if a "\n" exists
            sbuffer.append(ssrec.pop(0))
            if ssrec:
                break # Discard anything after the newline
        
        line = "".join(sbuffer)
        return line
        
        
    def receiveoneline(self):
        try:
            ret = json.loads(self.receiveonelinenj())
        except ValueError, e:
            raise Exception("%s:%s" % (e.message, text))
        assert "moredata" not in ret
        return ret
    