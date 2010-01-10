import scraperwiki

# converter here http://www.rutter.uklinux.net/ostowiki.html
print scraperwiki.geo.WGS84(56.0, -5.00, 200).latlng()
print scraperwiki.geo.OSGB("NS 13021 82624").latlng()


