#!/usr/bin/env python

import scraperwiki.sqlite

metadatamessagedone = False

def get(metadata_name, default=None):
    global metadatamessagedone
    if not metadatamessagedone:
        print "*** instead of metadata.get('%s') please use\n    scraperwiki.sqlite.get_var('%s')" % (metadata_name, metadata_name)
        metadatamessagedone = True
    return scraperwiki.sqlite.get_var(metadata_name, default)
    if result == metacallholder:
        result = get_client().get(metadata_name, default) 
    return result

def save(metadata_name, value):
    global metadatamessagedone
    if not metadatamessagedone:
        print "*** instead of metadata.get('%s') please use\n    scraperwiki.sqlite.get_var('%s')" % (metadata_name, metadata_name)
        metadatamessagedone = True
    return scraperwiki.sqlite.save_var(metadata_name, value)
