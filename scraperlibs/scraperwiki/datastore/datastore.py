# -*- coding: utf-8 -*-

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


        # a \n delimits the end of the record.  you cannot read beyond it or it will hang
def receiveoneline(socket):
    sbuffer = [ ]
    while True:
        srec = socket.recv(1024)
        if not srec:
            scraperwiki.console.dumpMessage({'message_type': 'chat', 'message':"socket from dataproxy has unfortunately closed"})
            break
        ssrec = srec.split("\n")  # multiple strings if a "\n" exists
        sbuffer.append(ssrec.pop(0))
        if ssrec:
            break
    line = "".join(sbuffer)
    return line



class DataStoreClass :

    def __init__(self, config) :
        self.m_socket = None
        self.m_config = config

    def connect(self, scraperID = ''):
        """
        Connect to the data proxy. The data proxy will need to make an Ident call
        back to get the scraperID. Since the data proxy may be on another machine
        and the peer address it sees will have been subject to NAT or masquerading,
        send the UML name and the socket port number in the request.
        """
        assert not self.m_socket
        if type(self.m_config) == types.StringType :
            conf = ConfigParser.ConfigParser()
            conf.readfp (open(self.m_config))
        else :
            conf = self.m_config
        host = conf.get    ('dataproxy', 'host')
        port = conf.getint ('dataproxy', 'port')
        self.m_socket    = socket.socket()
        self.m_socket.connect ((host, port))
        self.m_socket.sendall('GET /?uml=%s&port=%d&scraperid=%s HTTP/1.1\n\n' % (socket.gethostname(), self.m_socket.getsockname()[1], scraperID))
        
        line = receiveoneline(self.m_socket)  # comes back with True, "Ok"
        res = json.loads(line)
        assert res.get("status") == "good", res

    def request(self, req) :
        if not self.m_socket:
            self.connect()
        self.m_socket.sendall(json.dumps(req)+'\n')
        line = receiveoneline(self.m_socket)
        return json.loads(line)

    def save(self, unique_keys, scraper_data, date = None, latlng = None) :
        raise Exception("scraperwiki.datastore.save() has been deprecated.  Use scraperwiki.sqlite.save()")

    def save_sqlite(self, unique_keys, data, swdatatblname="swdata"):
        if unique_keys != None and type(unique_keys) not in [ types.ListType, types.TupleType ]:
            return { "error":'unique_keys must a list or tuple', "unique_keys_type":str(type(unique_keys)) }

        def convdata(unique_keys, scraper_data):
            if unique_keys:
                for key in unique_keys:
                    if key not in scraper_data:
                        return { "error":'unique_keys must be a subset of data', "bad_key":key }
                    if scraper_data[key] == None:
                        return { "error":'unique_key value should not be None', "bad_key":key }
            jdata = { }
            for key, value in scraper_data.items():
                if not key:
                    return { "error": 'key must not be blank', "bad_key":key }
                if type(key) not in [unicode, str]:
                    return { "error":'key must be string type', "bad_key":key }
                if not re.match("[a-zA-Z0-9_\- ]+$", key):
                    return { "error":'key must be simple text', "bad_key":key }
                
                if type(value) in [datetime.datetime, datetime.date]:
                    value = value.isoformat()
                elif value == None:
                    pass
                elif isinstance(value, SqliteError):
                    return {"error": str(value)}
                elif type(value) == str:
                    try:
                        value = value.decode("utf-8")
                    except:
                        return {"error": "Binary strings must be utf-8 encoded"}
                elif type(value) not in [int, bool, float, unicode, str]:
                    value = unicode(value)
                jdata[key] = value
            return jdata
                

        if type(data) == dict:
            rjdata = convdata(unique_keys, data)
            if rjdata.get("error"):
                return rjdata
        else:
            rjdata = [ ]
            for ldata in data:
                ljdata = convdata(unique_keys, ldata)
                if ljdata.get("error"):
                    return ljdata
                rjdata.append(ljdata)
        return self.request({"maincommand":'save_sqlite', "unique_keys":unique_keys, "data":rjdata, "swdatatblname":swdatatblname})
    
    def close (self) :
        self.m_socket.sendall('.\n')  # what's this for?
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
    """
    Convert object to unicode string before truncating to 't' characters

    Returns result as UTF8 encoded byte string

    >>> strencode_trunc('Hello World', 5) == 'Hello...'
    True
    >>> strencode_trunc(1234567890, 5) == '12345...'
    True
    >>> strencode_trunc('abcd\xc3\x8cf', 5) == 'abcdÌ...'
    True
    """
    if type(v) == types.StringType:
        v = v.decode('utf-8')
    else:
        v = unicode(v)

    try:
        return strunc(v, t).encode('utf-8')
    except:
        return "---"


def ifsencode_trunc(v, t):
    if type(v) in [int, float]:
        return v
    return strencode_trunc(v, t)


def save(unique_keys, data, date=None, latlng=None, silent=False, table_name="swdata", verbose=2) :
    raise Exception("scraperwiki.datastore.save() has been deprecated.  Use scraperwiki.sqlite.save()")


def sqlitecommand(command, val1=None, val2=None, verbose=1):
    ds = DataStore(None)
    result = ds.request({"maincommand":'sqlitecommand', "command":command, "val1":val1, "val2":val2})
    if "error" in result:
        raise databaseexception(result)
    if "status" not in result and "keys" not in result:
        raise Exception("possible signal timeout: "+str(result))
    
    # list type for second field in message dump
    if verbose:
        if val2 == None:
            lval2 = [ ]
        elif type(val2) in [tuple, list]:
            lval2 = [ ifsencode_trunc(v, 50)  for v in val2 ]
        elif command == "attach":
            lval2 = [ val2 ]
        elif type(val2) == dict:
            lval2 = [ ifsencode_trunc(v, 50)  for v in val2.values() ]
        else:
            lval2 = [ str(val2) ]
        scraperwiki.console.logSqliteCall(command, val1, lval2)
    
    return result
    

class SqliteError(Exception):  pass
class NoSuchTableSqliteError(SqliteError):  pass

def databaseexception(errmap):
    mess = errmap["error"]
    for k, v in errmap.items():
        if k != "error":
            mess = "%s; %s:%s" % (mess, k, v)
    
    if re.match('sqlite3.Error: no such table:', mess):
        return NoSuchTableSqliteError(mess)
    return SqliteError(mess)
        

def save_sqlite(unique_keys, data, table_name="swdata", verbose=2):
    ds = DataStore(None)
    result = ds.save_sqlite(unique_keys, data, table_name)
    if "error" in result:
        raise databaseexception(result)

    if verbose >= 2:
        pdata = {}
        if type(data) == dict:
            for key, value in data.items():
                pdata[strencode_trunc(key, 50)] = strencode_trunc(value, 50)
        elif data:
            for key, value in data[0].items():
                pdata[strencode_trunc(key, 50)] = strencode_trunc(value, 50)
            pdata["number_records"] = "Number Records: %d" % len(data)
            
        scraperwiki.console.logScrapedData(pdata)
    
    return result

