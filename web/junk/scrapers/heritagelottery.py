#!/usr/bin/python

import sys
import os
import datetime
import re
import urllib, urlparse
import feedparser

thisurl = "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py"

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


#<li>
#<a href="projects_directory/projects_by_region/north_east/durham/lych_gate_restoration/index.html" class="greysmallbold">Hillside Cemetery: Back to Life</a></li>
#<li>
def GetProjectsURLs():
    urlaz = "http://www.lhi.org.uk/a_to_z_listing.html"
    fin = urllib.urlopen(urlaz)
    hlpage = fin.read()
    fin.close()
    res = [ ]
    for s in re.findall('<li>\s*<a href="(projects_directory[^"]*)"[^>]*>([^<]*)</a>', hlpage):
        res.append((urlparse.urljoin(urlaz, s[0]), s[1]))
    return res


def ParseProjectData(hlpage):
    mtitle = re.search('<span class="blueevenbigger">(.*?)<br /></span>', hlpage)
    #<span class="standard">Heritage Lottery Fund: L5,538</span>
    # filtering out poind sign nonsense
    mgrant = re.search('<span class="standard">Heritage Lottery Fund: [^\d]{0,8}([\d,]+)</span>', hlpage)
    #if not mgrant:
    #    print re.findall('<span class="standard">.*', hlpage)
    mpostcode = re.search('<tr>\s*<td[^>]*><strong>Project Postcode\s</strong></td>\s*<td[^>]*><img[^>]*></td>\s*<td[^>]*><span[^>]*>([A-Z0-9\s]+)</span>', hlpage)

    mfinishdate = re.search('<tr>\s*<td[^>]*><strong>Finishing Date\s</strong></td>\s*<td[^>]*><img[^>]*></td>\s*<td[^>]*>([^<]*)</span>', hlpage)

    money = mgrant and int(re.sub(",", "", mgrant.group(1))) or 0
    postcode = mpostcode and mpostcode.group(1) or ""
    title = mtitle.group(1)
    finishdate = ""
    if mfinishdate:
        etime = feedparser._parse_date_rfc822(mfinishdate.group(1))
        if etime:
            finishdate = datetime.datetime(etime[0], etime[1], etime[2], 12, 0).isoformat()
        else:
            print "\n\n\n  ", mfinishdate.group(1)
    return title, money, postcode, finishdate

def UpdateHeritageLottery():
    urlps = GetProjectsURLs()
    for i in range(130, len(urlps)):
        print i, urlps[i][1],
        fin = urllib.urlopen(urlps[i][0])
        hlpage = fin.read()
        fin.close()
        title, money, postcode, finishdate = ParseProjectData(hlpage)
        if postcode:
            messid, mess = AddEntry({"src":"heritagelottery", "url":urlps[i][0],
                      "title":title, "postcode":postcode, "quantity":money,
                      "non_replace_field":"url", "evt_time":finishdate})
            print finishdate, messid, mess
        else:
            print "*** no postcode ***"

if __name__ == "__main__":
    UpdateHeritageLottery()


