import settings 
import codewiki.models as models
from django.db import connection
import sys
import cgi
import urllib
import re
 
def r(a):
    return "<tr><td>%s</td></tr>" % "</td><td>".join(a)
    

def WritePartyYears(party):
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT election, count(*), sum(votes) AS svotes FROM candidate WHERE party='%s' GROUP BY election ORDER BY year" % party)
    print "<h2>Results for party: %s</h2>" % party

    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"
    for election, number, votes in cursor.fetchall():
        #sparty = cgi.escape(party).encode("ascii", "xmlcharrefreplace")
        #lparty = '<a href="P-%s">%s</a>' % (urllib.quote_plus(sparty), sparty)
        print r([election, str(number), str(votes)])
    print "</table>"

    
def WriteConstituencyYears():
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT constituency, count(*), sum(votes) AS svotes FROM candidate GROUP BY constituency ORDER BY svotes DESC")
    print "<h2>Results by constituency: %s</h2>" % party
    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for constituency, number, votes in cursor.fetchall():
        sconstituency = re.sub(" ", "_", constituency)
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s">WP: %s</a>' % (sconstituency, constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"

    
def WritePartyVotes():
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)

    cursor.execute("SELECT party, count(*), sum(votes) AS svotes FROM candidate GROUP BY party ORDER BY svotes DESC")
    print '<table id="vparty">'
    print "<tr><th>Party</th><th>Candidates</th><th>Votes</th><tr>"
    for party, number, votes in cursor.fetchall():
        sparty = cgi.escape(party).encode("ascii", "xmlcharrefreplace")
        lparty = '<a href="P-%s">%s</a>' % (urllib.quote_plus(sparty), sparty)
        print r([lparty, str(number), str(votes)])
    print "</table>"

    
if "render" in sys.argv:
    tail = len(sys.argv) == 4 and sys.argv[3] or ""
    if tail[:2] == "P-":
        party = urllib.unquote_plus(tail[2:])
        WritePartyYears(party)
        WriteConstituencyYears()
    else:
        print "<h2>tail: " + tail + "</h2>"
        WritePartyVotes()
    

