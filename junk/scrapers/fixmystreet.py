#!/usr/bin/python

import sys
import os
import datetime
import re
import urllib, urlparse
import feedparser

thisurl = "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py"
now = datetime.datetime.now()

def AddEntry(params):
    params["user_id"] = "goatchurch"
    params["user_password"] = "garfield"
    params["submit"] = "post"
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
def UpdateFixMyStreets(fcouncil, council):
    fin = urllib.urlopen("http://www.fixmystreet.com/rss/reports/%s" % fcouncil)
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
        print fcouncil, " -- ", fmsrec[0]
        AddEntry({"src":"fixmystreet", "evt_time":etime, "district":council,
                  "title":fmsrec[0], "url":fmsrec[3], "summary":fmsrec[4],
                  "lat":float(fmsrec[5]), "lon":float(fmsrec[6]),
                  "non_replace_field":"title evt_time"})

def GetCouncils():
    fin = urllib.urlopen("http://www.fixmystreet.com/reports")
    fcouncillist = fin.read()
    fin.close()
    return re.findall('<a href="/reports/([^"]*)">([^<]*)</a>', fcouncillist)

if __name__ == "__main__":
    lcou = GetCouncils()
    for fcouncil, council in lcou:
        UpdateFixMyStreets(fcouncil, council)


