from scraperwiki import datastore
datastore.save(unique_keys=['key'], data={ 'key' : 'key_1', 'message' : 'HELLO_1' })
datastore.save(unique_keys=['key'], data={ 'key' : 'key_2', 'message' : 'HELLO_2' })
print "SAVED"
data = datastore.fetch (unique_keys = { 'key' : 'key_1' })
print data[0]['data']['message']
data = datastore.fetch (unique_keys = { 'key' : 'key_2' })
print data[0]['data']['message']

