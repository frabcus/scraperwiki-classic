#!/usr/bin/env python

import httplib
import urllib
import os

try   : import json
except: import simplejson as json

class MetadataClient(object):
    def __init__(self):
        proxy_host, proxy_port = os.environ['http_proxy'][7:].split(':')
        self.connection = httplib.HTTPConnection(proxy_host, proxy_port)
        self.scraper_guid = os.environ['SCRAPER_GUID']
        self.run_id = os.environ['RUNID']
        self.metadata_host = os.environ['metadata_host']

    def _check_scraper_guid(self):
        if not self.scraper_guid:
            raise Exception('Metadata cannot be accessed before the scraper has been saved')

    def _get_metadata(self, metadata_name):
        self._check_scraper_guid()

        self.connection.connect()
        self.connection.request(url='http://%s/scrapers/metadata_api/%s/%s/' % (self.metadata_host, self.scraper_guid, urllib.quote(metadata_name)), method='GET')
        resp = self.connection.getresponse()
        if resp.status == 200:
            result = json.loads(resp.read())
            result['value'] = json.loads(result['value'])
            return result
        else:
            return None
        self.connection.close()

    def get(self, metadata_name, default=None):
        metadata = self._get_metadata(metadata_name)
        if metadata:
            return metadata['value']
        else:
            return default

    def get_run_id(self, metadata_name):
        metadata = self._get_metadata(metadata_name)
        if metadata:
            return metadata['run_id']

    def put(self, metadata_name, value):
        self._check_scraper_guid()

        if self.get(metadata_name):
            method = 'PUT'
        else:
            method = 'POST'

        parameters = {}
        parameters['run_id'] = self.run_id
        parameters['value'] = json.dumps(value)

        self.connection.connect()
        self.connection.request(url='http://%s/scrapers/metadata_api/%s/%s/' % (self.metadata_host, self.scraper_guid, urllib.quote(metadata_name)), 
                                method=method,
                                body=urllib.urlencode(parameters),
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response = self.connection.getresponse() # Make sure we have a response before closing the connection!
        self.connection.close()
        return response.read()


# defer construction of client
client = None
def get_client():
    global client
    if not client:
        client = MetadataClient()
    return client
    
    
def get(metadata_name, default=None):
    return get_client().get(metadata_name, default)

def get_run_id(metadata_name, default=None):
    return get_client().get(metadata_name, default)

def put(metadata_name, value):
    return get_client().put(metadata_name, value)
