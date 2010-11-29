#!/usr/bin/env python

import httplib
import urllib
import os

try   : import json
except: import simplejson as json

import scraperwiki.console

class MetadataClient(object):
    def __init__(self):
        self.metadata_host = os.environ['metadata_host']
        if ":" in self.metadata_host:
            proxy_host, proxy_port = self.metadata_host.split(':')
        else:
            proxy_host, proxy_port = self.metadata_host, 80
        
        self.connection = httplib.HTTPConnection(proxy_host, proxy_port)
        try    : self.scraper_guid = os.environ['SCRAPER_GUID']
        except : self.scraper_guid = None
        try    : self.run_id       = os.environ['RUNID']
        except : self.run_id       = None
        
        # make a fake local metadata for unsaved scraper (could fill in values from environ).  Perhaps save some in the session
        if not self.scraper_guid:
            self.metadata_local = { "title":'"Untitled Scraper"', "CPU limit":'100' }

    def _get_metadata(self, metadata_name):
        self.connection.connect()
        self.connection.request(url='/scrapers/metadata_api/%s/%s/' % (self.scraper_guid, urllib.quote(metadata_name)), method='GET')
        resp = self.connection.getresponse()
        if resp.status == 200:
            result = json.loads(resp.read())    # un-json twice (one for input, and one from piston's auto json-ing of the output)
            result['value'] = json.loads(result['value'])
            return result
        else:
            return None
        self.connection.close()

    def get(self, metadata_name, default=None):
        if not self.scraper_guid: # Scraper hasn't been saved yet
            return self.metadata_local.get(metadata_name, default)

        metadata = self._get_metadata(metadata_name)
        if metadata:
            return metadata['value']
        else:
            return default

    def get_run_id(self, metadata_name):
        metadata = self._get_metadata(metadata_name)
        if metadata:
            return metadata['run_id']

    def save(self, metadata_name, value):
        if not self.scraper_guid: # Scraper hasn't been saved yet
            scraperwiki.console.logWarning ('The scraper has not been saved yet. Metadata will not be persisted between runs')
            self.metadata_local[metadata_name] = value
            return

        if self.get(metadata_name) == None:
            method = 'POST'
        else:
            method = 'PUT'

        parameters = {}
        parameters['run_id'] = self.run_id
        parameters['value'] = json.dumps(value)

        self.connection.connect()
        self.connection.request(url='/scrapers/metadata_api/%s/%s/' % (self.scraper_guid, urllib.quote(metadata_name)), 
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

def save(metadata_name, value):
    return get_client().save(metadata_name, value)
