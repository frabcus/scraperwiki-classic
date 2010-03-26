from scraperwiki import datastore
datastore.save(unique_keys=['key'], data={ 'key' : 'key_1', 'message' : u'HELLO_1_\u2019' })
datastore.save(unique_keys=['key'], data={ 'key' : 'key_2', 'message' : u'HELLO_2_\u2013' })
print "OK"
