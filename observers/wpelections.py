import settings 
import codewiki.models as models
from django.db import connection
import sys
import cgi
import urllib
import re
 
rc = 0
def r(a):
    global rc
    rc += 1
    if (rc % 2) == 1:
        return "<tr><td>%s</td></tr>" % "</td><td>".join(a)
    else:
        return '<tr><td class="grey">%s</td></tr>' % '</td><td class="grey">'.join(a)
    

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

def WriteElection(election):
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT constituency, count(*), sum(votes) AS svotes FROM candidate WHERE election='%s' GROUP BY constituency ORDER BY constituency" % election)
    print "<h3>All votes cast in the election: %s</h3>" % election

    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for constituency, number, votes in cursor.fetchall():
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"
    

def WriteConstituency(constituency):
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT election, count(*), sum(votes) AS svotes FROM candidate WHERE constituency='%s' GROUP BY election ORDER BY year" % constituency)
    print "<h3>All votes cast in the constituency: %s</h3>" % constituency
    sconstituency = re.sub(" ", "_", constituency)
    print '<p>Go to <a href="http://en.wikipedia.org/wiki/%s">%s</a> on Wikipedia</p>' % (sconstituency, constituency)

    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"     
    for election, number, votes in cursor.fetchall():
        print r([election, str(number), str(votes)])
    print "</table>"
      
def WriteConstituencyYears():
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT constituency, count(*), sum(votes) AS svotes FROM candidate GROUP BY constituency ORDER BY svotes DESC")
    print "<h3>Total number of candidates and votes cast per constituency</h3>"
    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for constituency, number, votes in cursor.fetchall():
        sconstituency = re.sub(" ", "_", constituency)
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s">WP: %s</a>' % (sconstituency, constituency)
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"

def WriteElectionYears():
    cursor = connection.cursor()
    cursor.execute("USE %s" % settings.DATABASE_NAME)
    cursor.execute("SELECT election, count(*), count(DISTINCT constituency), sum(votes) AS svotes FROM candidate GROUP BY election ORDER BY year")
    print "<h3>Total number of candidates and votes cast per election</h3>"
    print '<table>'
    print "<tr><th>Election</th><th>Constituencies</th><th>Candidates</th><th>Votes</th><tr>"
    for election, number, nconstituencies, votes in cursor.fetchall():
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(nconstituencies), str(number), str(votes)])
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

    
if "render" in sys.argv:
    WriteHead()
    tail = len(sys.argv) == 4 and sys.argv[3] or ""
    if tail == "constituency":
        WriteConstituencyYears()
    if tail == "election":
        WriteElectionYears()
    elif tail[:2] == "P-":
        party = urllib.unquote_plus(tail[2:])
        WritePartyYears(party)
    elif tail[:2] == "C-":
        constituency = urllib.unquote_plus(tail[2:])
        WriteConstituency(constituency)
    elif tail[:2] == "E-":
         election = urllib.unquote_plus(tail[2:])
         WriteElection(election)
    else:
        if tail:
            print "<h2>tail: " + tail + "</h2>"
        print "<h3>Total number of candidates and votes fielded in all Parliamentary elections</h3>"
        print '<p>See <a href="constituency">count per constituency</a> or <a href="election">count per election</a></p>'
        WritePartyVotes()
    print "</body>"
    print "</html>"
    

