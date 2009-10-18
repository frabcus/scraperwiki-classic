#!/usr/bin/python

import sys
import os
import datetime
import re
import urllib, urlparse
import feedparser
from optparse import OptionParser

hfields = ["user_id", "user_password", "src", "district", "postcode", "refid", "url", "evt_time", "title", "summary", "related_messid", "non_replace_field" ]
thisurl = "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py"
now = datetime.datetime.now()

def AddEntry(params):
    params["user_id"] = "goatchurch"
    params["user_password"] = "garfield"
    params["submit"] = "post"
    assert "src" in params
    assert "title" in params
    fin = urllib.urlopen(thisurl, urllib.urlencode(params))
    res = fin.read()
    fin.close()
    mres = re.search("<tr><td>messid</td><td>(\d+)( new)?</td></tr>", res)
    if mres:
        messid = int(mres.group(1))
        return messid, mres.group(2) and ":added:" or ":present:"
    print res
    return messid, "\n\n*** Failed ***\n"

def Datewithoutyear(day, month):
    fdate = "%s %s %d" % (day, month, now.year)
    etime = feedparser._parse_date_rfc822(fdate)
    etime = datetime.datetime(etime[0], etime[1], etime[2], 12, 0)
    if etime and etime <= now:
        return etime
    fdate = "%s %s %d" % (day, month, now.year - 1)
    etime = feedparser._parse_date_rfc822(fdate)
    etime = datetime.datetime(etime[0], etime[1], etime[2], 0, 0)
    return etime


#<item>
#<title>Poor road markings on dangerous junction, 10th September</title>
#<link>http://www.fixmystreet.com/?id=8616</link>
#<description>Sefton resurfaced Trafalgar/York Road (between Grosvenor Road and Weld Road) with poor quality cheapo finish which melted in the summer sun obscuring the road markings at the junction indicated.  They also didn't bother to paint the lines back up the middle of the road.  Quite shocking considering the number of accidents at this junction.
#&lt;br&gt;&lt;img src=&quot;http://www.fixmystreet.com/photo?id=8616&quot;&gt;</description>
#<guid isPermaLink="false">http://www.fixmystreet.com/?id=8616</guid>
#<georss:point>53.6303739206629 -3.0213209311559</georss:point>
#</item>
def UpdateFixMyStreets(council):
    fin = urllib.urlopen("http://www.fixmystreet.com/rss/reports/%s" % council)
    fms = fin.read()
    fin.close()

    refms = """(?x)<item>\s*
               <title>([^>]*?),\s+(\d+)(?:st|nd|rd|th)\s+([A-Z][a-z]+)</title>\s*
               <link>([^<]*)</link>\s*
               <description>([^<]*)</description>\s*
               <guid[^<]*</guid>\s*
               <georss:point>([\d\.\-]*)\s+([\d\.\-]*)</georss:point>\s*
               </item>
            """
    fmsrecs = re.findall(refms, fms)
    for fmsrec in fmsrecs:
        etime = Datewithoutyear(fmsrec[1], fmsrec[2])
        AddEntry({"src":"fixmystreet", "evt_time":etime, "district":council,
                  "title":fmsrec[0], "url":fmsrec[3], "summary":fmsrec[4],
                  "lat":float(fmsrec[5]), "lon":float(fmsrec[6]),
                  "non_replace_field":"title evt_time"})

#    <item>
#<title>The Anchorage, 1 bedroom flat (&#163;129,950)</title>
#<link>http://ononemap.com/go/25572982</link>
#<guid isPermaLink="false">OOM#25572982</guid>
#<pubDate>Tue, 11 Sep 2007 23:00:00 GMT</pubDate>
#</item>
def UpdateOnonemap(lat, lon):
    degdist = 0.02
    url = "http://ononemap.com/myfeed.rss?x1=%f&y1=%f&x2=%f&y2=%f&minbeds=0&maxbeds=99&minprice=0&maxprice=10000&proptype=&proxdistance=0&proxmultiplier=0.000568181818&proxtype=&maptype=Sales" % (lon - degdist, lat - degdist, lon + degdist, lat + degdist)
    fin = urllib.urlopen(url)
    oom = fin.read()
    fin.close()

    reoom = """(?x)<title>([^<]*?)\s*\(&\#163;([\d,]+)\)</title>\s*
               <link>([^<]*)</link>\s*
               <guid[^<]*</guid>\s*
               <pubDate>([^<]*)</pubDate>
            """
    foom = re.findall(reoom, oom)
    for foomrec in foom:
        money = int(re.sub(",", "", foomrec[1]))
        etime = feedparser._parse_date_rfc822(foomrec[3])
        etime = datetime.datetime(etime[0], etime[1], etime[2], etime[3], etime[4])
        AddEntry({"src":"ononemap", "evt_time":etime,
                  "title":foomrec[0], "url":foomrec[2], "quantity":money,
                  "lat":lat, "lon":lon,
                  "non_replace_field":"title lat lon"})




#<item rdf:about="http://gb.en-gb.pledgebank.com/LondonBookClub">
#<title>start a book club in Hampstead London</title>
#<link>http://gb.en-gb.pledgebank.com/LondonBookClub</link>
#<description>'I will start a book club in Hampstead London but only if 5 other Londoners will attend the first meeting.' -- HBC, Hampstead Book Club</description>
#<geo:lat>51.55</geo:lat>
#<geo:long>-0.1833333</geo:long>
#</item>
def UpdatePledgebank(postcode, c):
    url = "http://gb.en-gb.pledgebank.com/rss/list"
    #url = "http://gb.en-gb.pledgebank.com/rss/search?q=%s" % postcode
    fin = urllib.urlopen(url)
    pb = fin.read()
    fin.close()

    repb = """(?x)<title>([^<]*?)</title>\s*
                  <link>([^<]*?)</link>\s*
                  <description>'I\swill\s(.*?)'\s--\s([^<]*)</description>\s*
                  (?:<geo:lat>([\-\d\.]*)</geo:lat>\s*)?
                  (?:<geo:long>([\-\d\.]*)</geo:long>\s*)?
           """

    lpb = re.findall("(?s)(<item[\s>].*?</item>)", pb)
    n = 0
    for llpb in lpb:
        mpb = re.search(repb, llpb)
        if not mpb:
            print llpb
            return
        slat, slon =  mpb.group(5), mpb.group(6)
        if slat and slon:
            etime = now   # should be the time for pledge to close
            comma = re.search(",", mpb.group(4)) and "," or ""
            comma = ":"
            summary = "%s%s will %s" % (mpb.group(4), comma, mpb.group(3))
            summary = dbescape(summary)
            n += AddEntry(c, float(slat), float(slon), "pledgebank", 0, etime, mpb.group(2), 0, mpb.group(1), summary)
    print "Added %d of %d records from pledgebank" % (n, len(lpb))

#<p>Justin McKeating, the Pledge Creator, joined by:</p>
#<ul><li id="signer83268">Tim Ireland</li>
#<li id="signer83269">Neil Bell</li>
#<li id="signer83270" class="done">Andrew Shepard</li>
#<li id="signer83271">Dave Cross</li>
#<li id="signer83290">Barbara Goodsell</li><li id="signer83296">Chris Chrisostomou</li>
#<li id="signer83349">Rob Fahey</li></ul>
def UpdatePledgesigners(messid, c):
    c.execute("SELECT lat, lon, url, title, summary FROM metro_feed WHERE messid=%s" % messid)
    lat, lon, url, title, summary = c.fetchone()
    msummary = re.search(" will (.*?) but only if (\d+) (.*)", summary)
    if not msummary:
        print summary
    ntot = int(msummary.group(2))
    fin = urllib.urlopen(url)
    ps = fin.read()
    fin.close()
    psl = re.findall('<li id="signer\d+">([^<]*)</li>', ps)
    nrem = int(msummary.group(2)) - len(psl)
    sbut = (nrem >= 1 and (" but only if %d more %s" % (nrem, msummary.group(3))) or "")
    n = 0
    for psr in psl:
        stitle = '%s signed "%s"' % (psr, title)
        ssummary = '%s will %s%s' % (psr, msummary.group(1), sbut)
        n += AddEntry(c, lat, lon, "pledgebanksign", messid, now, url, 0, stitle, ssummary)
    return n

def UpdatePledgesigning(c):
    # do the pledge signers
    c.execute("SELECT messid FROM metro_feed WHERE src='pledgebank' ORDER BY evt_time LIMIT 30")
    a = c.fetchall()
    n = 0
    for m in a:
        n += UpdatePledgesigners(m[0], c)
    print "Added %d signers to pledges in pledgebank" % n


# reverse engineered from
# http://www.awardsforallgrants.org.uk:8080/a4a-search/afa_gs_1.xsql
def UpdateAwardsforallgrants():
    p = { "down_all":"Y", "ctrreg":"UK",  "intctr":"",
                   "frm_yr":"2008", "frm_mth":"02",
                   "amt_pred":"ALL",
                   "max_rows":"10",
                   "initv":"Awards for All",
                   "to_yr":"2008", "to_mth":"04",
                   "fprog":"",
                   "const":"",
                   "laarea":"",
                   "down_all":"Y", }
    url = "http://www.awardsforallgrants.org.uk:8080/a4a-search/afa_gs_7.xsql"
    fin = urllib.urlopen(url, urllib.urlencode(p))
    spreadsht = fin.read()
    fin.close()
    rows = re.findall("<tr><td>(.*?)</td></tr>", spreadsht)
    for row in rows:
        place, money, sdate, initiative, programme, district, region, country, constituency, summary = row.split("</td><td>")

        # unfortunately we don't get the sequence number so we can't go to the page like so
        seq = 121943
        url = "http://www.awardsforallgrants.org.uk:8080/a4a-search/afa_gs_5.xsql?seq=%d" % seq
        etime = datetime.datetime(int(sdate[6:10]), int(sdate[3:5]), int(sdate[0:2]), 7, 0, 0)
        AddEntry({"src":"awardsforall", "district":district,
                  "title":place, "summary":summary, "evt_time":etime, "url":url,
                  "quantity":money,
                  "non_replace_field":"title evt_time"})


#<a href="lancashire/cuerden_valley_park_community_wildlife_heritage_project/index.html" class="greysmallbold">Cuerden Valley Park Community Wildlife Heritage Pr</a>
def UpdateHeritageLottery():
    url = "http://www.lhi.org.uk/projects_directory/projects_by_region/north_west/index.html"
    fin = urllib.urlopen(url)
    hlpage = fin.read()
    fin.close()
    for s in re.findall('<li><a href="([^"]*)"[^>]*>([^<]*)</a>', hlpage):
        urlp = urlparse.urljoin(url, s[0])
        money = 1000
        AddEntry({"src":"heritagelottery", "url":urlp, "title":s[1], "non_replace_field":"title"})


# metro_upcoming - hardcoded events from
# http://www.freesteel.co.uk/metro_upcoming.html
def UpdateUpcoming(c):
    fin = urllib.urlopen("http://www.freesteel.co.uk/metro_upcoming.html")
    tab = fin.read()
    fin.close()
    for row in re.findall("<tr><td>(.*?)</td></tr>", tab):
        sdate, url, event, place, postcode = row.split("</td><td>")
        lat, lon =  PostcodePos(postcode, c)
        etime = datetime.datetime(int(sdate[0:4]), int(sdate[5:7]), int(sdate[8:9]), 18, 0, 0)
        AddEntry(c, lat, lon, "upcoming", 0, etime, url, 0, event, "Some event, prob the council")



# <div class="caption"><a href="detail.asp?region=NW&amp;dsid=1339">James has been missing from Manchester since 19 March 2008. He may be in Liverpool.</a></div>
def UpdateMissingPage(page, region):
    url = "http://www.missingpeople.org.uk/areyoumissing/missing/default.asp?page=%d&region=%s" % (page, region)
    fin = urllib.urlopen(url)
    misspage = fin.read()
    fin.close()
    if page != 1 and re.search("<strong>page 1 of 5</strong>", misspage):
        return []
    # the photo has the surname in it as well, but keep it simple
    for s in re.findall('<div class="caption"><a href="(detail.asp[^"]*)">([^<]*)</a></div>', misspage):
        urlp = urlparse.urljoin(url, s[0])
        mdate = re.search("((?:\d+) )?([JFMAMJJASOND][a-z]+),? ([12]\d\d\d)", s[1])
        if mdate:
            #print mdate.group(0)
            etime = feedparser._parse_date_rfc822((mdate.group(1) or "1") + " " + mdate.group(2) + " " + mdate.group(3))
            etime = datetime.datetime(etime[0], etime[1], etime[2], etime[3], etime[4])
        else:
            etime = now  # but we will parse from the entry

        AddEntry({"src":"missingpeople", "evt_time":etime, "district":region,
                  "title":s[1], "url":urlp,
                  "non_replace_field":"title"})


def UpdateMissing():
    #c.execute("DELETE FROM metro_feed WHERE src = 'missingpeople'")
    for page in range(1, 10):
        UpdateMissingPage(page, "NW")

# <span class="box-headers">Robbery in Sutton Heath</span><br>
# <a href="march/kh28-03a-sutton-heath.htm" class="bodytext">27/03 | Merseyside Police in St Helens has issued CCTV stills in relation to a robbery at the Texaco...</a>
def UpdateWanted():
    url = "http://www.merseyside.police.uk/html/news/crimestoppers/wanted/index.htm"
    fin = urllib.urlopen(url)
    wantpage = fin.read()
    fin.close()
    for s in re.findall('<span class="box-headers">([^<]*)</span><br>[^<]*<a href="([^"]*)" class="bodytext">([^<]*)</a>', wantpage):
        urlp = urlparse.urljoin(url, s[1])
        AddEntry({"src":"wanted", "district":"merseyside",
                  "title":s[0], "url":urlp, "summary":s[2],
                  "non_replace_field":"title url"})



parser = OptionParser()
parser.set_usage("""


Scrapes the different feeds into the database

args

    fixmystreet  download the potholes directory
    ononemap     download the house-sales directory
    pledgebank   update the pledges directory (incl signups)
    lottery      update lottery grants information
    upcoming     future events, eg council meetings (hard-coded)
    missingpeople missing people database
    wanted       police wanted
    heritagelottery update heritage lottery grants

  todo:
    planning     www.planningalerts.com
    foirequests  from www.whatdotheyknow.com for the council
    topix        local news feeds
    parliament   MP speeches and SIs tagged to the area
    groups       www.groupsnearyou.com (I don't think much of this)
    floods       flood warings and other environmental alerts
                   http://www.environment-agency.gov.uk/subjects/flood/floodwarning/
    observances  possibly sourced from 
                   http://en.wikipedia.org/wiki/Category:United_Nations_observances


example -- to scrape the houses for sale close to Cambridge into the database:
> python metrodb.py --postcode=CB44HW ononemap

""")

parser.add_option("--postcode", dest="postcode", metavar="postcode", default="l17ay",
                  help="postcode on which to centre the scrapings")
parser.add_option("--town", dest="town", metavar="town", default="Liverpool",
                  help="town on which to centre the scrapings")
parser.add_option("--council", dest="council", metavar="council", default="Sefton",
                  help="council on which to centre the scrapings")
parser.add_option("--quiet",
                  action="store_true", dest="quiet", default=False,
                  help="low volume messages")

if __name__ == "__main__":
    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    if "fixmystreet" in args:
        UpdateFixMyStreets(options.council)
    if "ononemap" in args:
        UpdateOnonemap(lat, lon)
    if "pledgebank" in args:
        UpdatePledgebank(options.postcode, c)
        UpdatePledgesigning(c)
    if "lottery" in args:
        UpdateAwardsforallgrants()
    if "upcoming" in args:
        UpdateUpcoming(c)
    if "missingpeople" in args:
        UpdateMissing()
    if "wanted" in args:
        UpdateWanted()
    if "heritagelottery" in args:
        UpdateHeritageLottery()

