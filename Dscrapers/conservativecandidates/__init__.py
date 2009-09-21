# New file
from scraperutils import RScrapeCachedURL
import re
import urlparse 
from codewiki.models import ScraperModule, DynElection
from django.db.models import Count, Sum
import urllib



def ss(d):
    return re.sub("<", "&lt;", str(d))

# This function is called when you click on the "Scrape" button.  
# Used for webcrawling the pages you are going to parse in the next stage.
# The RScrapeCachedURL() function downloads a page and caches it in a Reading object with some extra tags
# You can see all Reading objects at http://www.goatchurch.org.uk/scraperwiki/readings
def Scrape():
    # get page of all Conservative Party candidates
    urli = "http://www.conservatives.com/People/Prospective%20Parliamentary%20Candidates.aspx?&by=All"
    reading = RScrapeCachedURL(scraper_tag="conservative_index", name="all", url=urli)
    soup = reading.soup()

    # extract the number for verification
    mcandidatecount = re.search("There are currently (\d+) Prospective Parliamentary Candidates", str(soup))
    assert mcandidatecount, "Didn't find candidate count all index page"
    
    # verify the heading of the table is what it should be
    ppcrows = soup.table.findAll("tr")
    headrow = [ "".join(th.contents).strip()  for th in ppcrows[0].findAll("th") ]
    assert headrow == ["Name", "Constituency"], "Head mismatch: " + ss(ppcrows[0])

    # loop through each row
    assert len(ppcrows) - 1 == int(mcandidatecount.group(1)), "Reported rows mismatch"
    for tr in ppcrows[1:]:
        lurl = tr.td.a["href"]
        name = "".join(tr.td.a.contents)
        constituency = "".join(tr.td.nextSibling.contents)
        constituency = re.sub(" & ", " and ", constituency)
        print ss([lurl, name, constituency])
        urlp = urlparse.urljoin(urli, lurl)

        # scrape the page for each candidate into the cache, and tag it with "conservative_candidate" so we can find it later
        ppcreading = RScrapeCachedURL(scraper_tag="conservative_candidate", name=name, url=urlp)
        print len(ppcreading.contents()), ss([lurl, name, constituency])


# This function is run against every Reading in the database to filter those which the Parse() function will parse
# Click on the "DoesApplyAll" button to create the list of all Readings that we are intending to parse
# Click on one of those links to make it possible to run singly.  
def DoesApply(reading):
    return reading.scraper_tag == "conservative_candidate"

def DescParse(d):
    mdp = re.match("(Member of Parliament|Prospective Parliamentary Candidate) for (.*)$", d)
    assert mdp, "Does not match desc: " + d
    return mdp.group(1), mdp.group(2)    

# This function is called on a particular Reading when you click on the "ParseSingle" button
# It should return a list of maps that are inserted into the keyvalue database.
def Parse(reading):
    soup = reading.soup()   # get the text loaded into a BeautifulSoup object
    maintxt = soup.find("div", "main-txt")  # pull out the div containing the text
    name = "".join(maintxt.h1.contents)     # h1 contains the name
    h2contents = maintxt.h2.contents        # h2 contains positions separated by <br/>
    h3contents = maintxt.h3.contents
    if h3contents:
        print "*****", ss(h3contents)       # h3 rarely used

    # one or two positions are limited per candidate, except Alun Cairns where there is a mistake
    params = { "name":name }    
    print ss(h2contents)
    if len(h2contents) != 0:
        assert h2contents[1].name == "br"
        k, v = DescParse(h2contents[0])
        params[k] = v
        if len(h2contents) == 4:
            k, v = DescParse(h2contents[2])
            params[k] = v
            assert h2contents[3].name == "br"
        else:
            assert len(h2contents) == 2
    else:
        assert name == "Alun Cairns"

    # extract the email and webpage links for the candidate
    for abld in maintxt.findAll("a", "bld"):
        hbld = abld["href"]
        if hbld[:7] == "mailto:":
            params["email"] = hbld[7:]
            assert params["email"] == abld.contents[0]
        elif hbld[:7] == "http://":
            params["web"] = hbld
            assert hbld[7:] == re.sub("http://", "", abld.contents[0]), ("Mismatch web:", ss(abld), params["web"], abld.contents)

    params["url"] = reading.url
    
    # there is only one record per page, so we return a list of length one
    return [ params ]



rc = 0
def r(a):
    global rc
    rc += 1
    #return "".join(["<tr><td>", str(a), "</td></tr>"])
    if (rc % 2) == 1:
        return u"<tr><td>%s</td></tr>" % u"</td><td>".join(a)
    else:
        return u'<tr><td class="grey">%s</td></tr>' % u'</td><td class="grey">'.join(a)

def WriteHead():
    print "<html>"
    print "<head>"
    print '<style type="text/css">'
    print 'table {border-collapse: collapse; }'
    print 'td {border: thin black solid; }'
    print 'td.grey {background-color: #e8e8e8; }'
    print 'th {background-color: black;  color: white; }'
    print '</style>'
    print '</head>'
    print '<body>'


def Observe(tailurl):
    election = "next United Kingdom general election"
    party = "Conservative Party (UK)"
    wpconst = { }
    for qs in DynElection.objects.filter(election=election, party=party).all():
        wpconst[qs.constituency] = qs.candidate.encode("ascii", "xmlcharrefreplace")
    
    WriteHead()
    scrapermodule = ScraperModule.objects.get(modulename="conservativecandidates") 
    print '<table>'
    print "<tr><th>Name</th><th>WP entry</th><th>Constituency</th><th>email</th><th>webpage</th></tr>"
    clist = [ ]
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        kv = detection.contents()[0]
        lastname = re.match("(\S+)\s+(.*)$", kv.get("name")).group(2)
        constituency = kv.get("Prospective Parliamentary Candidate", "")
        #clist.append((lastname, kv))
        clist.append((constituency, kv))
    clist.sort()
    for n, kv in clist:
        constituency = kv.get("Prospective Parliamentary Candidate", "")
        wpconstituency = constituency + " (UK Parliament constituency)"
        wpcan = wpconst.get(wpconstituency, "")
        lname = '<a href="%s">%s</a>' % (kv.get("url"), kv.get("name"))
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s#Elections_of_the_2000s">%s</a>' % (re.sub(" ", "_", wpconstituency), constituency)
        web = kv.get("web", "")
        lweb = web and '<a href="%s">%s</a>' % (web, web[7:]) or ""
        print r([lname, wpcan, lconstituency, kv.get("email", ""), lweb])
    print "</table>"
    

    

