#!/usr/bin/env python

import httplib
import urllib
import os
import json

class MetadataClient(object):
    def __init__(self):
        proxy_host, proxy_port = os.environ['http_proxy'][7:].split(':')
        self.connection = httplib.HTTPConnection(proxy_host, proxy_port)
        self.scraper_guid = os.environ['SCRAPER_GUID']
        self.run_id = os.environ['RUNID']

    def get(self, metadata_name, default=None):
        self.connection.connect()
        self.connection.request(url='http://metadata.scraperwiki.com/scrapers/metadata_api/%s/%s/' % (self.scraper_guid, urllib.quote(metadata_name)), method='GET')
        resp = self.connection.getresponse()
        if resp.status == 200:
            result = json.loads(resp.read())
            result['value'] = json.loads(result['value'])
            return result
        else:
            print resp.msg
            return default
        self.connection.close()

    def put(self, metadata_name, value):
        if self.get(metadata_name):
            method = 'PUT'
        else:
            method = 'POST'

        parameters = {}
        parameters['run_id'] = self.run_id
        parameters['value'] = json.dumps(value)

        self.connection.connect()
        self.connection.request(url='http://metadata.scraperwiki.com/scrapers/metadata_api/%s/%s/' % (self.scraper_guid, urllib.quote(metadata_name)), 
                                method=method,
                                body=urllib.urlencode(parameters),
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        self.connection.getresponse() # Make sure we have a response before closing the connection!
        self.connection.close()


client = MetadataClient()

def get(metadata_name, default=None):
    return client.get(metadata_name, default)

def put(metadata_name, value):
    return client.put(metadata_name, value)
