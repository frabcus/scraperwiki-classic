# -*- coding: utf-8 -*-

import  string
import  socket
import  urllib
import  cgi
import  datetime
import  types
import  socket
import  re
import scraperwiki

try   : import json
except: import simplejson as json

import scraperwiki

m_socket = None
m_host = None
m_port = None

        # make everything global to the module for simplicity as opposed to half in and half out of a single class
def create(host, port):
    global m_host
    global m_port
    m_host = host
    m_port = int(port)

        # a \n delimits the end of the record.  you cannot read beyond it or it will hang
def receiveoneline(socket):
    sbuffer = [ ]
    while True:
        srec = socket.recv(1024)
        if not srec:
            scraperwiki.dumpMessage({'message_type': 'chat', 'message':"socket from dataproxy has unfortunately closed"})
            break
        ssrec = srec.split("\n")  # multiple strings if a "\n" exists
        sbuffer.append(ssrec.pop(0))
        if ssrec:
            break
    line = "".join(sbuffer)
    return line


def ensure_connected():
    global m_socket
    if not m_socket:
        m_socket = socket.socket()
        m_socket.connect((m_host, m_port))
        m_socket.sendall('GET /?uml=%s&port=%d HTTP/1.1\n\n' % (socket.gethostname(), m_socket.getsockname()[1]))
        line = receiveoneline(m_socket)  # comes back with True, "Ok"
        res = json.loads(line)
        assert res.get("status") == "good", res

def request(req):
    ensure_connected()
    m_socket.sendall(json.dumps(req)+'\n')
    line = receiveoneline(m_socket)
    return json.loads(line)


def close():
    m_socket.sendall('.\n')  # what's this for?
    m_socket.close()
    m_socket = None



# old apiwrapper functions, used in the general emailer (though maybe should be inlined to that file)
apiurl = "http://api.scraperwiki.com/api/1.0/"

def getInfo(name, version=None, history_start_date=None, quietfields=None):
    query = {"name":name}
    if version:
        query["version"] = version
    if history_start_date:
        query["history_start_date"] = history_start_date
    if quietfields:
        query["quietfields"] = quietfields
    url = "%sscraper/getinfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def getRunInfo(name, runid=None):
    query = {"name":name}
    if runid:
        query["runid"] = runid
    url = "%sscraper/getruninfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def getUserInfo(username):
    query = {"username":username}
    url = "%sscraper/getuserinfo?%s" % (apiurl, urllib.urlencode(query))
    ljson = urllib.urlopen(url).read()
    return json.loads(ljson)

def save(unique_keys, data, date=None, latlng=None, silent=False, table_name="swdata", verbose=2) :
    raise Exception("scraperwiki.datastore.save() has been deprecated.  Use scraperwiki.sqlite.save()")

def getKeys(name):
    raise scraperwiki.sqlite.SqliteError("getKeys has been deprecated")

def getData(name, limit=-1, offset=0):
    raise scraperwiki.sqlite.SqliteError("getData has been deprecated")

def getDataByDate(name, start_date, end_date, limit=-1, offset=0):
    raise scraperwiki.sqlite.SqliteError("getDataByDate has been deprecated")

def getDataByLocation(name, lat, lng, limit=-1, offset=0):
    raise scraperwiki.sqlite.SqliteError("getDataByLocation has been deprecated")
    
def search(name, filterdict, limit=-1, offset=0):
    raise scraperwiki.sqlite.SqliteError("apiwrapper.search has been deprecated")

