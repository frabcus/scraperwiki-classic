import  os
import  urllib2
import  scraperwiki
print   urllib2.urlopen("http://127.0.0.1:9001/Option?runid=%s&a=1&b=1" % os.environ['RUNID']).read()
scraperwiki.cache (True)

