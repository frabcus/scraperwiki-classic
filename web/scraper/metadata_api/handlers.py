#!/usr/bin/env python

from piston.handler import BaseHandler
from piston.utils import rc
from scraper.models import Scraper, ScraperMetadata

class ScraperMetadataHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'PUT')
    model = ScraperMetadata
    fields = ('name', 'value', 'run_id')

    def read(self, request, scraper_guid, metadata_name):
        try:
            scraper = Scraper.objects.get(guid=scraper_guid)
            metadata = scraper.scrapermetadata_set.get(name=metadata_name)
            return metadata
        except:
            return rc.NOT_HERE

    def create(self, request, scraper_guid, metadata_name):
        if not 'run_id' in request.POST or not 'value' in request.POST:
            print "Bad Request - create"
            return rc.BAD_REQUEST

        scraper = Scraper.objects.get(guid=scraper_guid) 

        if scraper.scrapermetadata_set.filter(name=metadata_name).count() > 0:
            print "Duplicate entry"
            return rc.DUPLICATE_ENTRY

        metadata = ScraperMetadata()
        metadata.name = metadata_name
        metadata.scraper = scraper
        metadata.run_id = request.POST['run_id']
        metadata.value = request.POST['value']
        metadata.save()

        return metadata

    def update(self, request, scraper_guid, metadata_name):
        if not 'run_id' in request.PUT or not 'value' in request.PUT:
            print "Bad Request - update"
            return rc.BAD_REQUEST

        try:
            scraper = Scraper.objects.get(guid=scraper_guid)
            metadata = scraper.scrapermetadata_set.get(name=metadata_name)
        except:
            return rc.NOT_HERE

        metadata.run_id = request.PUT['run_id']
        metadata.value = request.PUT['value']
        metadata.save()

        return metadata
