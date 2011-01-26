import  settings
import  socket
import  urllib

try   : import json
except: import simplejson as json


class DataStoreClass :

    def __init__ (self) :

        self.m_socket   = None
        self.m_host     = settings.DATAPROXY_HOST
        self.m_port     = settings.DATAPROXY_PORT

    def connect (self, scraperID, short_name) :

        """
        Connect to the data proxy.
        """

        self.m_socket    = socket.socket()
        self.m_socket.connect ((self.m_host, self.m_port))
        data = [ ("uml", socket.gethostname()), ("port", self.m_socket.getsockname()[1]), ("scraperid", scraperID), ("short_name", short_name) ]
        self.m_socket.send ('GET /?%s HTTP/1.1\n\n' % urllib.urlencode(data))
        rc, arg = json.loads (self.m_socket.recv (1024))
        if not rc : raise Exception (arg)

    def request (self, req) :
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

    def data_dictlist (self, limit = 1000, offset = 0, start_date = None, end_date = None, latlng = None) :

        if start_date is not None : start_date = str(start_date)
        if end_date   is not None : end_date   = str(  end_date)
        if latlng     is not None : latlng     = '%010.6f,%010.6f' % tuple(latlng)

        return self.request (('data_dictlist', limit, offset, start_date, end_date, latlng))

    def clear_datastore (self) :

        return self.request (('clear_datastore',))

    def datastore_keys (self) :

        return self.request (('datastore_keys',))

    def data_search (self, key_values, limit, offset) :

        return self.request (('data_search', key_values, limit, offset))

    def item_count (self) :

        return self.request (('item_count',))

    def has_geo (self) :

        return self.request (('has_geo',))

    def has_temporal (self) :

        return self.request (('has_temporal',))

    def recent_record_count (self, days) :

        return self.request (('recent_record_count', days))

    def close (self) :

        self.m_socket.send ('.\n')
        self.m_socket.close()
        self.m_socket = None


def DataStore (scraperID, short_name) :
    ds = DataStoreClass()
    ds.connect (scraperID, short_name)
    return ds
