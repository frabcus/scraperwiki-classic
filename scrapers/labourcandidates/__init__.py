# New file
from scraperutils import RScrapeCachedURL
import re
import urlparse 
from codewiki.models import ScraperModule, DynElection
from django.db.models import Count, Sum
import urllib

rc = 0

##########################################################################
# This function is called when you click on the "Scrape" button.  
# Used to crawl the pages you are going to parse in the next stage
# The RScrapeCachedURL() function called here downloads a page and caches it in a Reading object with some extra tags
# You can see all Reading objects downloaded at http://www.goatchurch.org.uk/scraperwiki/readings
def Scrape():

    # get page of all Labour Party candidates
    urli = "http://www.labour.org.uk/ppc?Page=%d"
    
    #get page and put it into Reading object
    for i in range(1, 15):
        reading = RScrapeCachedURL(scraper_tag="labour_index", name="page_%d"%i, url=urli%i)       
        soup = reading.soup()
    
        # extract the list of candidates
        swclist = soup.find("ul", "swc_List")
        # ... and find the individual entries in the list
        ppcrows = swclist.findAll("li")

        #TODO - any verification here?
    
        # loop through each row
        for li in ppcrows[1:]:
            #get PPC name, constituency, and HTML page
            lurl = li.a["href"]
            #name_and_constituency = li.a.contents 
            m = re.match("(?:Councillor )?(.*?), PPC for (.*)$", li.a.contents[0])
            name = m.group(1)
            constituency = m.group(2)
            urlp = urlparse.urljoin(urli, lurl)
            print ss([lurl, name, constituency])
            # scrape the individual HTML page for each candidate into the cache, and tag it with "labour_candidate" so we can find it later
            ppcreading = RScrapeCachedURL(scraper_tag="labour_candidate", name=name, url=urlp)
            print len(ppcreading.contents()), ss([lurl, name, constituency])                     
    return 

#replace left-brackets with character entities
def ss(d):
    return re.sub("<", "&lt;", str(d))

##########################################################################
# Parse individual pages
# This function is run against every Reading in the database to filter those which the Parse() function will parse
# Click on the "DoesApplyAll" button to create the list of all Readings that we are intending to parse
# Then, click on one of those links to run parsing singly 
def DoesApply(reading):
    return reading.scraper_tag == "labour_candidate"

# This function is called on a particular Reading when you click on the "ParseSingle" button
# It should return a list of maps that are inserted into the keyvalue database.
# Params are : name, address, email, web, url
def Parse(reading):
    soup = reading.soup()   # get the text loaded into a BeautifulSoup object
    
    #get name
    nametxt = soup.find("div", "menu_content_title")  # pull out the div containing the name text
    
    #handle exceptions
    maincontent = soup.find("div", "main_content")
    if re.search("Sorry, the request could not be completed.", str(maincontent)):
        assert re.search("hannah_cooper|oliver_de_botton", reading.url), reading.url
        return [ ]
    
    mname = "".join(nametxt.h1.contents)     # h1 contains the name
    params = { "name":mname }
    
    maintxt = soup.find("div", "main_news_content_text")
    strmaintxt = str(maintxt)

    mconstituency = re.search("<h6></h6>\s*PPC for (.*?)<br />", strmaintxt)
    assert mconstituency
    params["constituency"] = mconstituency.group(1)
                             
    maddress = re.search("<strong>Write to me at:</strong><br />(.*?)<br />", strmaintxt)
    if maddress:
        params["address"] = maddress.group(1).strip()
    
    mphone = re.search("<strong>Phone me on:</strong><br />(.*?)<br />", strmaintxt)
    if mphone:
        params["phone"] = mphone.group(1).strip()
        
    memail = re.search('<strong>Email me at:</strong><br /><a href="mailto:(.*?)"', strmaintxt)
    if memail:
        params["email"] = memail.group(1).strip()
        
    mweb = re.search('<strong>Website address:</strong><br /><a href="(.*?)"', strmaintxt)
    if mweb:
        params["web"] = mweb.group(1).strip()

    params["url"] = reading.url
        
    # there is only one record per page, so we return a list of length one
    return [ params ]

# Called from within Parse function - match description
def DescParse(d):
    mdp = re.match("(Member of Parliament|Prospective Parliamentary Candidate) for (.*)$", d)
    assert mdp, "Does not match desc: " + d
    return mdp.group(1), mdp.group(2)    

##########################################################################
# Observe - prints out scraped results from database in a readable form
# Called by clicking on Observe link
def Observe(tailurl):
    election = "next United Kingdom general election"
    party = "Labour Party (UK)"
    wpconst = { }
    for qs in DynElection.objects.filter(election=election, party=party).all():
        wpconst[qs.constituency] = qs.candidate.encode("ascii", "xmlcharrefreplace")
        
    #output the header
    WriteHead()
    
    scrapermodule = ScraperModule.objects.get(modulename="labourcandidates") 
    
    #print table headings
    print '<table>'
    print "<tr><th>Name</th><th>WP entry</th><th>Address</th><th>Phone number</th><th>Constituency</th><th>Email</th><th>Webpage</th></tr>"
    clist = [ ]
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        kvs = detection.contents()
        if not kvs:  # Hannah Cooper's
            continue
        kv = kvs[0]
        lastname = kv.get("name", "")
        constituency = kv.get("constituency", "")
        clist.append((lastname, kv))
        #clist.append((constituency, kv))
    clist.sort()
    kvprev = None
    for n, kv in clist:
        if kvprev and kvprev["name"] == kv["name"]:
             continue    # get rid of duplicates
        constituency = kv.get("constituency", "")
        wpconstituency = constituency + " (UK Parliament constituency)"
        wpcan = wpconst.get(wpconstituency, "")
        lname = '<a href="%s">%s</a>' % (kv.get("url"), kv.get("name"))
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s#Elections_of_the_2000s">%s</a>' % (re.sub(" ", "_", wpconstituency), constituency)
        web = kv.get("web", "")
        lweb = web and '<a href="%s">%s</a>' % (web, web[7:]) or ""
        print r([lname, wpcan, lconstituency, kv.get("address", ""),  kv.get("phone", ""), kv.get("email", ""), lweb])
        kvprev = kv
    print "</table>"
    
    


#HTML page header and style info - called from Observe function
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

# called from Observe function
def r(a):
    global rc
    rc += 1
    #return "".join(["<tr><td>", str(a), "</td></tr>"])
    if (rc % 2) == 1:
        return u"<tr><td>%s</td></tr>" % u"</td><td>".join(a)
    else:
        return u'<tr><td class="grey">%s</td></tr>' % u'</td><td class="grey">'.join(a)
    
    
#
