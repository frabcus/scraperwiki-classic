#!/usr/bin/python

import sys
import os
import datetime
import re
import urllib, urlparse
import cgi, cgitb
cgitb.enable()
from misc import PostcodePos, ConstituencyPos
from misc import GetCursorDB, dbescape

from lonlat2mercator import *


now = datetime.datetime.now()
thisurl = "http://www.freesteel.co.uk/cgi-bin/hackday/hackdaydb.py"

def CreateTables():
    c = GetCursorDB()
    print "Creating TABLE hackday_event"
    c.execute("DROP TABLE IF EXISTS hackday_event")
    mcols = [ "messid INT not null primary key auto_increment",
              "lat FLOAT", "lon FLOAT", "district TEXT", "postcode VARCHAR(20)", 
              "src TEXT",     # type eg fixmystreet, pledgebank
              "refid TEXT",           # id of message we refer to (eg if it's a pledge comment)
              "evt_time DATETIME", "rec_time DATETIME",
              "url TEXT", "quantity FLOAT", 
              "title TEXT", "summary TEXT", 
              "related_messid INT", # related event (used for linked events, to join table with itself)
              "user_id VARCHAR(20)" ]
    c.execute("CREATE TABLE hackday_event (%s)" % ", ".join(mcols))


    print "Creating TABLE hackday_mess"
    c.execute("DROP TABLE IF EXISTS hackday_mess")
    scols = [ "messid INT", "act VARCHAR(5)", # such as c=clicked, s=seen
              "lat FLOAT", "lon FLOAT",
              "see_time DATETIME", 
              "user_id VARCHAR(20)", 
              "unique(messid, lat, lon, user_id)", ]
    c.execute("CREATE TABLE hackday_mess (%s)" % ", ".join(scols))

    print "Creating TABLE hackday_user"
    c.execute("DROP TABLE IF EXISTS hackday_user")
    scols = [ "user_id VARCHAR(20)", "user_password TEXT", "user_email TEXT", "comments TEXT",
              "unique(user_id)" ]
    c.execute("CREATE TABLE hackday_user (%s)" % ", ".join(scols))
    c.execute("INSERT INTO hackday_user (user_id, user_password, user_email, comments)" + 
              "VALUES ('goatchurch', 'garfield', 'julian@freesteel.co.uk', 'this is me')")


def CreateCacheTables():
    c = GetCursorDB()
    print "Creating TABLE hackday_postcode_cache"
    c.execute("DROP TABLE IF EXISTS hackday_postcode_cache")
    c.execute("CREATE TABLE hackday_postcode_cache (postcode VARCHAR(20), constituency TEXT, lat FLOAT, lon FLOAT)")

    print "Creating Table hackday_constituency_cache"
    c.execute("DROP TABLE IF EXISTS hackday_constituency_cache")
    c.execute("CREATE TABLE hackday_constituency_cache (constituency TEXT, lat FLOAT, lon FLOAT)")



def WriteFormLine(para, comment=""):
    print '<tr><td>%s</td><td><input type="TEXT" name="%s"></td><td>%s</td></tr>' % (para, para, comment)


def WriteForm():
    Writehead("formentry")
    print '<form action="%s" method="post">' % thisurl
    print '<table>'
    WriteFormLine("user_id")
    WriteFormLine("user_password")
    WriteFormLine("user_email", "when adding new user")
    WriteFormLine("src", "source or type of event")
    WriteFormLine("lat", "GPS latitude (float)")
    WriteFormLine("lon", "GPS longitude (float)")
    WriteFormLine("district", "to clear records enter 'delete all src'")
    WriteFormLine("postcode")
    WriteFormLine("refid", "reference id used in the source database")
    WriteFormLine("url", "link for the event")
    WriteFormLine("evt_time", "time of the event")
    WriteFormLine("quantity", "float value (eg monetary amount)")
    WriteFormLine("title", "title of the event")
    WriteFormLine("summary", "extra text description")
    WriteFormLine("related_messid", "messid of a related event (eg to event begins)")
    WriteFormLine("non_replace_field", "don't save record matching this field exists")
    print '</table>'
    print '<input type="SUBMIT" name="submit" value="submit">'
    print '</form>'


def GetParam(form, para):
    return form.has_key(para) and form[para].value or ""

def GetParamI(form, para):
    ff = GetParam(form, para)
    return re.match("[+\-]?[0-9]+$", ff) and int(ff) or 0

def GetUserPassword(c, form):
    user_id = dbescape(GetParam(form, "user_id"))
    if not user_id:
        return "", ""
    if len(user_id) > 18:
        return "", "user_id too long"
    user_password = dbescape(GetParam(form, "user_password"))
    if not user_password:
        return "", "blank password"
    c.execute("SELECT user_password FROM hackday_user WHERE user_id='%s'" % user_id)
    a = c.fetchone()
    if a:
        if a[0] == user_password:
            return user_id, ""   # an actual login!!!
        else:
            return "", "Wrong password"
    user_email = GetParam(form, "user_email")
    if not re.search("\S+@\S+$", user_email):
        return "", "New user please supply email"
    user_comment = GetParam(form, "title")

    c.execute("""REPLACE INTO hackday_user 
                 (user_id, user_password, user_email, comments)
                 VALUES ('%s', '%s', '%s', '%s')
              """ % (user_id, user_password, dbescape(user_email), dbescape(user_comment)))

    return "", "New user '%s' added" % user_id

def SubmitValues(c, form, user_id):
    dbfields = ["user_id", "src", "district", "postcode", "refid", "url", "evt_time", "rec_time", "title", "summary", "related_messid" ]
    dbffields = ["lat", "lon", "quantity"]
    dbmap = { }
    for dbfield in dbfields:
        dbmap[dbfield] = dbescape(GetParam(form, dbfield))
    for dbfield in dbffields:
        vv = dbescape(GetParam(form, dbfield))
        dbmap[dbfield] = re.match("[+\-]?[0-9.]+$", vv) and float(vv) or 0.0
    for ff in ["related_messid",]:
        dbmap[ff] = re.match("[+\-]?[0-9]+$", dbmap[ff]) and int(dbmap[ff]) or 0
    for ff in ["evt_time",]:
        mdt = re.match("(\d\d\d\d)-(\d\d)-(\d\d)", dbmap[ff])
        if mdt:
            dt = datetime.datetime(int(mdt.group(1)), int(mdt.group(2)), int(mdt.group(3)), 0, 0)
            dbmap[ff] = dt.isoformat()
        else:
            dbmap[ff] = ""
    dbmap["rec_time"] = now.isoformat()
    dbmap["user_id"] = user_id
    if (not dbmap["lat"] and not dbmap["lon"] and dbmap["postcode"]):
        dbmap["lat"], dbmap["lon"] = PostcodePos(dbmap["postcode"], c)

    non_replace_field = GetParam(form, "non_replace_field")
    if non_replace_field:
        qwhere = " AND ".join(["%s='%s'" % (nrf, dbmap[nrf])  for nrf in non_replace_field.split()  if nrf in dbmap])
        c.execute("SELECT messid FROM hackday_event WHERE %s" % qwhere)
        a = c.fetchone()
        if a:
            return int(a[0]), False

    # build the db query for posting the data into hackday_event
    vals = [ "'%s'" % dbmap[s]  for s in dbfields ]
    vals[-1] = "%d" % dbmap[dbfields[-1]]
    vals.extend([ "%f" % dbmap[s]  for s in dbffields ])

    dbfields.extend(dbffields)
    query = "REPLACE INTO hackday_event (%s) VALUES (%s)" % (", ".join(dbfields), ", ".join(vals))
    #print "<p>", query, "</p>"
    c.execute(query)

    # need to get the unique key out
    c.execute("SELECT messid FROM hackday_event WHERE rec_time='%s' and title='%s'" % (dbmap["rec_time"], dbmap["title"]))
    a = c.fetchone()
    return int(a[0]), True

def DeleteAllSrc(c, userid, src):
    a = c.execute("DELETE FROM hackday_event WHERE user_id='%s' AND src='%s'" % (userid, src))
    return "Deleted %d %s entries of user %s" % (a, src, userid)

def WriteVals(c, messid, bentered):
    Writehead("oneval")
    dbfields = ["messid", "user_id", "src", "district", "postcode", "refid", "url", "evt_time", "rec_time", "title", "summary", "related_messid", "lat", "lon", "quantity"]
    c.execute("SELECT %s FROM hackday_event WHERE messid=%d" % (", ".join(dbfields), messid))
    a = c.fetchone()
    print "<table border=\"1\">"
    for i in range(len(dbfields)):
        if i == 0 and bentered:
            print "<tr><td>%s</td><td>%s new</td></tr>" % (dbfields[i], a[i])
        else:
            print "<tr><td>%s</td><td>%s</td></tr>" % (dbfields[i], a[i])
    print "</table>"

def WriteListPerUser(c, listuser_id):
    Writehead("listperuser")
    print "<h3>List of sources for userid: <i>%s</i></h3>" % listuser_id
    print "<table>"
    c.execute("SELECT src, COUNT(*) AS c FROM hackday_event WHERE user_id='%s' GROUP BY src ORDER BY c DESC" % dbescape(listuser_id))
    for a in c.fetchall():
        print '<tr><td><a href="%s?listuser=%s&listsrc=%s">%s</a></td><td>%d</td></tr>' % (thisurl, listuser_id, a[0], a[0], a[1])
    print "</table>"

def WriteListUser(c, listuser_id, listsrc):
    Writehead("listuser")
    print '<h3>List of values for userid: <i>%s</i>  src: <i>%s</i></h3>' % (listuser_id, listsrc)
    print "<table>"
    c.execute("SELECT messid, url, title, rec_time FROM hackday_event WHERE user_id='%s' AND src='%s' ORDER BY rec_time DESC" % (dbescape(listuser_id), dbescape(listsrc)))
    print "<tr><th>messid</th><th>title</th><th>rec_time</th></tr>"
    for a in c.fetchall():
        print '<tr><td><a href="%s?messid=%d">%d</a></td>' % (thisurl, a[0], a[0])
        if a[1]:
            print '<td><a href="%s">%s</a></td>' % (a[1], a[2])
        else:
            print '<td>%s</td>' % (a[2])
        print '<td>%s</td>' % a[3]
        print '</tr>'
    print "</table>"

def Writehead(typ):
    print "Content-type: text/html\n";
    print "<html>"
    print "<head>"
    print '<meta http-equiv="content-type" content="text/html; charset=iso-8859-1">'
    print '<title>Hackday common database tool</title>'
    print '<link href="/hackday.css" type="text/css" rel="stylesheet" media="all">'
    print '<body class="%s">' % typ
    if typ == "frontpage":
        print "<h1>Hackday common database tool</h1>"
    else:
        print '<h1><a href="%s">Hackday common database tool</a></h1>' % thisurl


def WriteFront(c, usermess):
    Writehead("frontpage")
    if usermess:
        print '<h2 class="mess">%s</h2>' % usermess
    print '<ul>'
    print '<li><a href="%s?act=listusers">See list of users and numbers of records</a></li>' % thisurl
    print '<li><a href="%s?act=submit">Submit a record through a form or make new user</a></li>' % thisurl
    print '<li><a href="%s?act=osmform">Build queries for downloading messages</a></li>' % thisurl
    print '<li><a href="http://code.google.com/p/metroscope/">Source, instructions and examples on code.google</a></li>'
    print '</ul>'

def WriteListUsers(c):
    Writehead("listusers")
    c.execute("""SELECT hackday_user.user_id, user_email, COUNT(*) AS c, comments 
                 FROM hackday_user 
                 LEFT JOIN hackday_event ON hackday_event.user_id = hackday_user.user_id 
                 GROUP BY user_id ORDER BY c DESC""")
    print "<table>"
    print "<tr><th>user_id</th><th>email</th><th>number of records</th><th>comments</th></tr>"
    for a in c.fetchall():
        print '<tr><td><a href="%s?listuser=%s">%s</a></td><td>%s</td><td>%d</td><td>%s</td></tr>' % (thisurl, a[0], a[0], a[1], a[2], a[3])
    print "</table>"

def WriteOSMlayer(c, form):
    format = GetParam(form, "format")
    user_id = dbescape(GetParam(form, "user"))
    src = dbescape(GetParam(form, "src"))

    # these limits are not applied in the database query because that requires the lat,lon to be in the merc format
    r = 0
    sllat, sllon, sr = GetParam(form, "lat"), GetParam(form, "lon"), GetParam(form, "r")
    if re.match("[+\-\d\.]+$", sllat) and re.match("[+\-\d\.]+$", sllon) and re.match("[\d\.]", sr):
        llat, llon, r = float(sllat), float(sllon), float(sr)
    slimit = GetParam(form, "limit")
    limit = re.match("\d+$", slimit) and int(slimit) or 100
    
    print "Content-type: text/plain\n";
    qlwhere = [ ]
    if src:
        qlwhere.append("src='%s'" % src)
    if user_id:
        qlwhere.append("user_id='%s'" % user_id)
    print "lat\tlon\ticon\ticonSize\ticonOffset\tdescription\ttitle"
    c.execute("SELECT lat, lon, src, url, title, quantity FROM hackday_event WHERE %s" % " AND ".join(qlwhere))
    for a in c.fetchall():
        lat, lon = a[0], a[1]
        if format == "merc":
            lat, lon = merc_y(lat), merc_x(lon)
        if r and (abs(lat - llat) > r or abs(lon - llon) > r):
            continue        

        # here's where we need to print different formats
        fpng = "%s_icon.png" % a[2]
        if src == "heritagelottery":
            fsize = "20,20\t0,-20"
        else:
            fsize = "24,24\t0,-24"
        ftext = "<a href=\"%s\">%s</a>" % (a[3], a[4])
        print "%f\t%f\t%s\t%s\t%s\t%s" % (lat, lon, fpng, fsize, ftext, a[2])

        # limit can't be done in dbase query because the filtering by merc_x projection
        limit -= 1
        if limit < 0:
            break

def WriteOSMform():
    Writehead("osmformquery")
    print "<p>For testing the form printing of data</p>"
    print '<form action="%s" method="get">' % thisurl
    print '<table>'
    WriteFormLine("format", "must be set, use 'merc'")
    WriteFormLine("user", "user_id of data")
    WriteFormLine("src", "filtering by this tag")
    WriteFormLine("limit", "number of entries in return table")
    WriteFormLine("r", "radius from lat lon (optional)")
    WriteFormLine("lat", "present when r exists")
    WriteFormLine("lon", "present when r exists")
    print '</table>'
    print '<input type="SUBMIT" name="submit" value="query">'
    print '</form>'


if __name__ == "__main__":
    form = cgi.FieldStorage()
    pathpartstr = (os.getenv("PATH_INFO") or '').strip('/')
    pathparts = [ s  for s in pathpartstr.split('/')  if s ]
    referrer = os.getenv("HTTP_REFERER") or ''
    ipaddress = os.getenv("REMOTE_ADDR") or ''
    useragent = os.getenv("HTTP_USER_AGENT") or ''
    
    c = GetCursorDB()
    if GetParam(form, "format"):
        WriteOSMlayer(c, form)
        sys.exit(0)
        
    passuser_id, usermess = GetUserPassword(c, form)
    
    messid = GetParamI(form, "messid")
    act = GetParam(form, "act")
    listuser_id = GetParam(form, "listuser")
    listsrc = GetParam(form, "listsrc")

    bentered = False
    if passuser_id:
        if GetParam(form, "submit") in [ "submit", "post" ]:
            src = GetParam(form, "src")
            if src and GetParam(form, "district") == "delete all src":
                usermess = DeleteAllSrc(c, passuser_id, src)
            elif src and GetParam(form, "title"):
                messid, bentered = SubmitValues(c, form, passuser_id)
            else:
                usermess = "record must at least have source and title"
    if messid:
        WriteVals(c, messid, bentered)
    elif act == "submit":
        WriteForm()
    elif act == "listusers":
        WriteListUsers(c)
    elif act == "osmform":
        WriteOSMform()
    elif listuser_id:
        if listsrc:
            WriteListUser(c, listuser_id, listsrc)
        else:
            WriteListPerUser(c, listuser_id)
    else:
        WriteFront(c, usermess)

    print "</body>\n</html>"



