import	scraperwiki
import	BeautifulSoup
from	scraperwiki import datastore

html = scraperwiki.scrape('http://scraperwiki.com/hello_world.html')
page = BeautifulSoup.BeautifulSoup(html)

for table in page.findAll('table'):
    for row in table.findAll('tr')[1:]:
        datastore.save(unique_keys=['message'], data={'message' : row.td.string,})
