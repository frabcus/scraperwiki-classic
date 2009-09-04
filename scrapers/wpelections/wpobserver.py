import settings 
from codewiki.models import ScraperModule, DynElection
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
    query_set = DynElection.objects.extra(select={'election':'election', 'count':'count(1)', 'svotes':'sum(votes)' }, 
                                  order_by=['-year'], where=["party='%s'" % party]).values('election', 'count', 'svotes')
    query_set.query.group_by = ['election']
    print "<h2>Results for party: %s</h2>" % party

    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in query_set.all():
        election, number, votes = qs["election"], qs["count"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(number), str(votes)])
    print "</table>"

def WriteElection(election):
    query_set = DynElection.objects.extra(select={'constituency':'constituency', 'count':'count(1)', 'svotes':'sum(votes)' }, 
                                 order_by=['constituency'], where=["election='%s'" % election]).values('constituency', 'count', 'svotes')
    query_set.query.group_by = ['constituency']
    print "<h3>All votes cast in the election: %s</h3>" % election

    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in query_set.all():
        constituency, number, votes = qs["constituency"], qs["count"], qs["svotes"]
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"
    

def WriteConstituency(constituency):
    query_set = DynElection.objects.extra(select={'election':'election', 'count':'count(1)', 'svotes':'sum(votes)' }, 
                                order_by=['-year'], where=["constituency='%s'" % constituency]).values('election', 'count', 'svotes')
    query_set.query.group_by = ['election']
    
    print "<h3>All votes cast in the constituency: %s</h3>" % constituency
    sconstituency = re.sub(" ", "_", constituency)
    print '<p>Go to <a href="http://en.wikipedia.org/wiki/%s">%s</a> on Wikipedia</p>' % (sconstituency, constituency)

    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"     
    for qs in query_set.all():
        election, number, votes = qs["election"], qs["count"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(number), str(votes)])
    print "</table>"
      
def WriteConstituencyYears():
    query_set = DynElection.objects.extra(select={'constituency':'constituency', 'count':'count(1)', 'svotes':'sum(votes)' }, 
                                order_by=['-svotes']).values('constituency', 'count', 'svotes')
    query_set.query.group_by = ['constituency']

    print "<h3>Total number of candidates and votes cast per constituency</h3>"
    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in query_set.all():
        constituency, number, votes = qs["constituency"], qs["count"], qs["svotes"]
        sconstituency = re.sub(" ", "_", constituency)
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s">WP: %s</a>' % (sconstituency, constituency)
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"

    
def WriteElectionYears():
    query_set = DynElection.objects.extra(select={'election':'election', 'count':'count(1)', 'constituencies':'count(DISTINCT constituency)', 'svotes':'sum(votes)' }, 
                               order_by=['-year']).values('election', 'count', 'constituencies', 'svotes')
    query_set.query.group_by = ['election']

    print "<h3>TTotal number of candidates and votes cast per election</h3>"
    print '<table>'
    print "<tr><th>Election</th><th>Constituencies</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in query_set.all():
        election, number, nconstituencies, votes = qs["election"], qs["count"], qs["constituencies"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(nconstituencies), str(number), str(votes)])
    print "</table>"


def WritePartyVotes():
    query_set = DynElection.objects.extra(select={'party':'party', 'count':'count(1)', 'svotes':'sum(votes)' }, 
                               order_by=['-svotes']).values('party', 'count', 'svotes')
    query_set.query.group_by = ['party']

    print '<table id="vparty">'
    print "<tr><th>Party</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in query_set.all():
        party, number, votes = qs["party"], qs["count"], qs["svotes"]
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

    
def Observe(tail):
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
    

