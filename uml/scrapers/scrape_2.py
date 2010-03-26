import urllib2
html = urllib2.urlopen('http://scraperwiki.com/hello_world.html').read()
print html
