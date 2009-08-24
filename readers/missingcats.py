from detectors.scraperutils import ScrapeCachedURL

urlindex = "http://www.nationalpetregister.org/mp-cats.php?showold=yes"
scrapertag_index = "missingcats_index"
for i in range(40, 45):  # edit this to get different page ranges
    url = urlindex + "&page=" + str(i)
    text = ScrapeCachedURL(scraper_tag=scrapertag_index, name="page " + str(i), url=url)
    print i, len(text)
    





