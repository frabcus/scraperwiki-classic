import  string
import  socket
import  urllib
import  cgi
import  datetime
import  types
import  socket
import  ConfigParser

try   : import json
except: import simplejson as json



def mangleflattendict(data):
    rdata = { }
    for key, value in data.items() :
        
        # was previously mangled in dataproxy/datalib.fixKVKey()  kept for compatibility, 
        # but moved here to allow in future a function save_no_mangling()
        # or optional filtering that prevents invalid keys getting into scrapers that are intended to have xml output, 
        # so those that will never have xml output can avoid damage
        rkey = key.replace(' ', '_')  
        
        # in future this could be json.dumps or something that is better able to manage the 
        # confusion between unicode and str types (and mark them all up to unicode)
        if value == None:
            rvalue = u""
        elif value == True:
            rvalue = u"1"
        elif value == False:
            rvalue = u"0"
        elif isinstance(value, datetime.date):
            rvalue = value.isoformat()
        elif isinstance(value, datetime.datetime):
            rvalue = value.isoformat()
        elif type(value) == types.UnicodeType:
            rvalue = value
        elif type(value) == types.StringType:
            rvalue = value   # if we knew this was utf8 or latin-1 we'd be able to decode it into unicode!
        else:
            rvalue = unicode(value)   #
            
        rdata[rkey] = rvalue
    return rdata
        

def mangleflattenkeys(keys):
    rkeys = [ ]
    for key in keys:
        rkey = key.replace(' ', '_')  
        rkeys.append(rkey)
    return rkeys


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

    def fetch (self, unique_keys_dict) :

        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
            return [ False, 'unique_keys must a non-empty dictionary' ]

        uunique_keys_dict = mangleflattendict(unique_keys_dict)
        return self.request (('fetch', uunique_keys_dict))

    def retrieve (self, unique_keys_dict) :

        if type(unique_keys_dict) not in [ types.DictType ] or len(unique_keys_dict) == 0 :
            return [ False, 'unique_keys must a non-empty dictionary' ]

        uunique_keys_dict = mangleflattendict(unique_keys_dict)
        return self.request (('retrieve', uunique_keys_dict))
    
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
        
        # flatten everything into strings here rather than in the dataproxy/datalib where 
        js_data = mangleflattendict(scraper_data)

        # unique_keys need to be mangled too so that they match
        uunique_keys = mangleflattenkeys(unique_keys)
        
        return self.request (('save', uunique_keys, js_data, date, latlng))

    def postcodeToLatLng (self, postcode) :

        return self.request (('postcodetolatlng', postcode))

    def close (self) :

        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None


# manage local copy of the above class in the global space of this module
# (this function is first called from controller.execPython)
ds = None
def DataStore (config) :
    global ds
    if ds is None :
        ds = DataStoreClass(config)
    return ds


# functions moved from the out of date code into here to manage their development
def save (unique_keys, data, date = None, latlng = None, silent = False) :
    ds = DataStore(None)
    rc, arg = ds.save (unique_keys, data, date, latlng)
    if not rc :
        raise Exception (arg) 

    pdata = {}
    for key, value in data.items():
        try    : key   = str(key)
        except : key   = key  .encode('utf-8')
        try    : value = str(value)
        except : value = value.encode('utf-8')
        pdata[cgi.escape(key)] = cgi.escape(value)

    if not silent :
        print '<scraperwiki:message type="data">%s' % json.dumps(pdata)
    return arg


# undocumented fetch function
def fetch (unique_keys) :
    """undocumented - use at your own risk"""
    ds = DataStore(None)
    rc, arg = ds.fetch (unique_keys)
    if not rc :
        raise Exception (arg) 

    return arg


# undocumented retrieve function
def retrieve (unique_keys) :
    """undocumented - use at your own risk"""
    ds = DataStore(None)
    rc, arg = ds.retrieve (unique_keys)
    if not rc :
        raise Exception (arg) 

    return arg

