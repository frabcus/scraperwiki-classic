import  string
import  socket
import  urllib
import  datetime
import  types
import	socket
import	ConfigParser

try   : import json
except: import simplejson as json

class DataStoreClass :

    def __init__ (self, config) :

        self.m_socket    = None
        self.m_config    = config

    def connect (self) :

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
            self.m_socket.send ('GET /?uml=%s HTTP/1.1\n\n' % (socket.gethostname()))
            rc, arg = json.loads (self.m_socket.recv (1024))
            if not rc : raise Exception (arg)

    def request (self, req) :

        self.connect ()
        self.m_socket.send (json.dumps (req) + '\n')
        rc = self.m_socket.recv (1024)
        return json.loads (rc)

    def save (self, unique_keys, scraper_data, date = None, latlng = None) :

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
            except : value = str(value)
            js_data[key] = value

        return self.request (('save', unique_keys, js_data, date, latlng))

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
