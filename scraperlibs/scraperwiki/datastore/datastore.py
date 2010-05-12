import  string
import  socket
import  urllib
import  datetime
import  types
import  socket
import  ConfigParser

try   : import json
except: import simplejson as json

class DataStoreClass :

    def __init__ (self, config) :

        self.m_socket    = None
        self.m_config    = config

    def connect (self) :

        """
        Connect to the data proxy. The data proxy will need to make an Ident call
        back to get the scraperID. Since the data proxy may be on another machine
        and the peer address it sees will have been subject to NAT or masquerading,
        send the UML name and the socket port number in the request.
        """

        if not self.m_socket :
            if type(self.m_config) == types.StringType :
                conf = ConfigParser.ConfigParser()
                conf.readfp (open(self.m_config))
            else :
                conf = self.m_config
            host = conf.get    ('dataproxy', 'host')
            port = conf.getint ('dataproxy', 'port')
            self.m_socket    = socket.socket()
            self.m_socket.connect ((host, port))
            self.m_socket.send ('GET /?uml=%s&port=%d HTTP/1.1\n\n' % (socket.gethostname(), self.m_socket.getsockname()[1]))
            rc, arg = json.loads (self.m_socket.recv (1024))
            if not rc : raise Exception (arg)

    def request (self, req) :

        self.connect ()
        self.m_socket.send (json.dumps (req) + '\n')

        text = ''
        while True :
            data = self.m_socket.recv (1024)
            if len(data) == 0 :
                break
            text += data
            if text[-1] == '\n' :
                break

        return json.loads (text)

    def fetch (self, unique_keys) :

        if type(unique_keys) not in [ types.DictType ] or len(unique_keys) == 0 :
            return [ False, 'unique_keys must a non-empty dictionary' ]

        return self.request (('fetch', unique_keys))

    def save (self, unique_keys, scraper_data, date = None, latlng = None) :

        if type(unique_keys) not in [ types.NoneType, types.ListType, types.TupleType ] :
            return [ False, 'unique_keys must be None, or a list or tuple' ]
 
        if date   is not None :
            if type(date) not in [ datetime.datetime, datetime.date ] :
                return [ False, 'date should be a python.datetime (not %s)' % type(date) ]

        if latlng is not None :
            if type(latlng) not in [ types.ListType, types.TupleType ] or len(latlng) != 2 :
                return [ False, 'latlng must be a (float,float) list or tuple' ]
            if type(latlng[0]) not in [ types.IntType, types.LongType, types.FloatType ] :
                return [ False, 'latlng must be a (float,float) list or tuple' ]
            if type(latlng[1]) not in [ types.IntType, types.LongType, types.FloatType ] :
                return [ False, 'latlng must be a (float,float) list or tuple' ]

        if date   is not None :
            date   = str(date)
        if latlng is not None :
            latlng = '%010.6f,%010.6f' % tuple(latlng)

        #  Data must be JSON-encodable. Brute force attack, try each data value
        #  in turn and stringify any that bork.
        #
        js_data = {}
        for key, value in scraper_data.items() :
            try    : json.dumps (value)
            except : value = unicode(value)
            ukey = key.replace(' ', '_')  # was previously mangled in dataproxy/datalib.fixKVKey()
            js_data[ukey] = value

        if unique_keys:
            uunique_keys = [ key.replace(' ', '_')  for key in unique_keys ]
        else:
            uunique_keys = unique_keys
        return self.request (('save', uunique_keys, js_data, date, latlng))

    def close (self) :

        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None

ds = None

def DataStore (config) :

    global ds
    if ds is None :
        ds = DataStoreClass(config)
    return ds
