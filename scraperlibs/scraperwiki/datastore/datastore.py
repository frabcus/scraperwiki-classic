import  string
import  socket
import  urllib
import  cgi
import  datetime
import  types
import  socket
import  ConfigParser
import  re

try   : import json
except: import simplejson as json

import  scraperwiki.console

# handles old version of the key-value store
# intend to make a new sqlite module and access functions into there

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
            rvalue = unicode(value)
            
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

    def connect (self, scraperID = '') :

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
            self.m_socket.send ('GET /?uml=%s&port=%d&scraperid=%s HTTP/1.1\n\n' % (socket.gethostname(), self.m_socket.getsockname()[1], scraperID))
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

    def uses_old_datastore(self):
        return self.request(('item_count',))[1] != 0
    
    def save (self, unique_keys, scraper_data, date = None, latlng = None) :
        
        if type(unique_keys) not in [ types.NoneType, types.ListType, types.TupleType ] :
            return [ False, 'unique_keys must be None, or a list or tuple' ]
 
        if date is not None :
            if type(date) not in [ datetime.datetime, datetime.date ] :
                return [ False, 'date should be a python.datetime (not %s)' % type(date) ]

        if latlng is not None :
            if type(latlng) not in [ types.ListType, types.TupleType ] or len(latlng) != 2 :
                return [ False, 'latlng must be a (float,float) list or tuple' ]
            if type(latlng[0]) not in [ types.IntType, types.LongType, types.FloatType ] :
                return [ False, 'latlng must be a (float,float) list or tuple' ]
            if type(latlng[1]) not in [ types.IntType, types.LongType, types.FloatType ] :
                return [ False, 'latlng must be a (float,float) list or tuple' ]

        if date is not None :
            date = str(date)
        if latlng is not None :
            latlng = '%010.6f,%010.6f' % tuple(latlng)

        #  Data must be JSON-encodable. Brute force attack, try each data value
        #  in turn and stringify any that bork.
        
        #  Flatten everything into strings here rather than in the dataproxy/datalib.
        #  See comment against "mangleflattendict"
        #
        js_data = mangleflattendict (scraper_data)

        #  Unique_keys need to be mangled too so that they match
        #
        uunique_keys = mangleflattenkeys (unique_keys)
        
        return self.request (('save', uunique_keys, js_data, date, latlng))

    
    def save_sqlite(self, unique_keys, scraper_data, swdatatblname="swdata"):
        if type(unique_keys) not in [ types.ListType, types.TupleType ]:
            return [ False, 'unique_keys must a list or tuple' ]

        for key in unique_keys:
            if key not in scraper_data:
                return [ False, 'unique_keys must be a subset of data' ]

        jdata = { }
        for key, value in scraper_data.items():
            if not key:
                return [ False, 'key must not be blank' ]
            if type(key) not in [unicode, str]:
                return [ False, 'key must be string type' ]
            if not re.match("[a-zA-Z0-9_\- ]+$", key):
                return [ False, 'key must be simple text: '+key ]
            
            if type(value) in [datetime.datetime, datetime.date]:
                value = value.isoformat()
            elif type(value) not in [int, bool, float, unicode, str]:
                value = unicode(value)

            jdata[key] = value
        
        return self.request(('save_sqlite', unique_keys, jdata, swdatatblname))
    
    
    def postcodeToLatLng (self, postcode) :

        return self.request (('postcodetolatlng', postcode))

    def close (self) :

        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None


# manage local copy of the above class in the global space of this module
# (this function is first called from controller.exec.py where a little 3 line config file is locally generated -- in case you need help with the spaghetti)
ds = None
def DataStore (config) :
    global ds
    if ds is None :
        ds = DataStoreClass(config)
    return ds



def strunc(v, t):
    if not t or len(v) < t:
        return v
    return "%s..." % v[:t]

def strencode_trunc(v, t):
    try:
        return strunc(str(v), t)
    except:  
        pass
    try:
        return strunc(v, t).encode('utf-8')
    except:
        pass
    return "---"


def ifsencode_trunc(v, t):
    if type(v) in [int, float]:
        return v
    return strencode_trunc(v, t)


# functions moved from the out of data code into here to manage their development
def save(unique_keys, data, date = None, latlng = None, silent = False, verbose=2) :
    ds = DataStore(None)
    
    if silent:   # should deprecate soon
        verbose = 0
    
    # enable soon (new version wrapper)
    if False and not ds.uses_old_datastore():
        
        rc = True
        if date is not None:
            if type(date) not in [ datetime.datetime, datetime.date ] :
                rc, arg = False, 'date should be a python.datetime (not %s)' % type(date)

        if latlng is not None :
            if type(latlng) not in [ types.ListType, types.TupleType ] or len(latlng) != 2:
                rc, arg = False, 'latlng must be a (float,float) list or tuple'
            elif type(latlng[0]) not in [ types.IntType, types.LongType, types.FloatType ]:
                rc, arg = False, 'latlng must be a (float,float) list or tuple'
            elif type(latlng[1]) not in [ types.IntType, types.LongType, types.FloatType ]:
                rc, arg = False, 'latlng must be a (float,float) list or tuple'

        if date is not None :
            scraper_data["date"] = date.isoformat()
        if latlng is not None :
            scraper_data["latlng_lat"] = float(latlng[0])
            scraper_data["latlng_lng"] = float(latlng[1])
        
        if not rc:
            rc, arg = ds.save_sqlite(unique_keys, data, verbose=verbose)
        if not rc:
            raise Exception(arg) 
        return arg
    
    
    # old version
    rc, arg = ds.save(unique_keys, data, date, latlng)
    if not rc:
        raise Exception (arg) 
    
    if verbose:
        pdata = {}
        for key, value in data.items():
            pdata[strencode_trunc(key, 50)] = strencode_trunc(value, 50)
        scraperwiki.console.logScrapedData(pdata)
    return arg



def sqlitecommand(command, val1=None, val2=None, verbose=1):
    ds = DataStore(None)
    result = ds.request(('sqlitecommand', command, val1, val2))
    if "error" in result:
        raise Exception(result["error"])
    if "status" not in result and "keys" not in result:
        raise Exception("possible signal timeout: "+str(result))
    
    # list type for second field in message dump
    if verbose:
        if not val2:
            lval2 = [ ]
        elif type(val2) in [tuple, list]:
            lval2 = [ ifsencode_trunc(v, 50)  for v in val2 ]
        elif command == "attach":
            lval2 = [ val2 ]

        scraperwiki.console.logSqliteCall(command, val1, lval2)
    
    return result
    

def save_sqlite(unique_keys, data, table_name="swdata", commit="True", verbose=2):
    ds = DataStore(None)
    result = ds.save_sqlite(unique_keys, data, table_name)
    if "error" in result:
        raise Exception(result["error"]) 

    if commit:
        sqlitecommand("commit", None, None, 0)

    if verbose >= 2:
        pdata = {}
        for key, value in data.items():
            pdata[strencode_trunc(key, 50)] = strencode_trunc(value, 50)
        if not commit:
            pdata["commit"] = "NOT_COMMITTED"
        scraperwiki.console.logScrapedData(pdata)
    
    return result.get("status")

