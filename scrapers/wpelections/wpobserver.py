import settings 
from codewiki.models import ScraperModule, DynElection
import sys
import cgi
import urllib
import re
from django.db.models import Count, Sum
   
rc = 0
def r(a):
    global rc
    rc += 1
    if (rc % 2) == 1:
        return "<tr><td>%s</td></tr>" % "</td><td>".join(a)
    else:
        return '<tr><td class="grey">%s</td></tr>' % '</td><td class="grey">'.join(a)
    
    
def WritePartyYears(party):
    print "<h2>Results for party: %s</h2>" % party
    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in DynElection.objects.filter(party=party).values('election').annotate(count=Count('election'), svotes=Sum('votes')).order_by('-year'):
        election, number, votes = qs["election"], qs["count"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(number), str(votes)])
    print "</table>"

def WriteCandidate(candidate):
    lcandidate = candidate
    mwpcandidate = re.match("\[\[(.*?)\]\]", lcandidate)
    if mwpcandidate:
        wcandidate = re.sub(" ", "_", mwpcandidate.group(1))
        lcandidate = '<a href="http://en.wikipedia.org/wiki/%s">%s</a>' % (wcandidate, lcandidate)
    print "<h3>All votes cast for candidate: %s</h3>" % lcandidate

    print '<table>'
    print "<tr><th>Election</th><th>Constituency</th><th>Party</th><th>Votes</th><th>Winner</th><tr>"
    for qs in DynElection.objects.filter(candidate=candidate).all():
        election, constituency, party, votes, winner = qs.election, qs.constituency, qs.party, qs.votes, qs.winner
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)        
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lelection, lconstituency, party, str(votes), str(winner)])
    print "</table>"
    

def WriteConstituency(constituency):    
    print "<h3>All votes cast in the constituency: %s</h3>" % constituency
    sconstituency = re.sub(" ", "_", constituency)
    print '<p>Go to <a href="http://en.wikipedia.org/wiki/%s">%s</a> on Wikipedia</p>' % (sconstituency, constituency)

    print '<table>'
    print "<tr><th>Election</th><th>Candidates</th><th>Votes</th><tr>"     
    for qs in DynElection.objects.filter(constituency=constituency).values('election').annotate(count=Count('election'), svotes=Sum('votes')).order_by('-year'):
        election, number, votes = qs["election"], qs["count"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(number), str(votes)])
    print "</table>"

    
def WriteElection(election):
    print "<h3>All votes cast in the election: %s</h3>" % election
    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"     
    for qs in DynElection.objects.filter(election=election).values('constituency').annotate(count=Count('constituency'), svotes=Sum('votes')).order_by('constituency'):
        constituency, number, votes = qs["constituency"], qs["count"], qs["svotes"]
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"
    
    
def WriteConstituencyYears():
    print '<table>'
    print "<tr><th>Constituency</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in DynElection.objects.values('constituency').annotate(count=Count('constituency'), svotes=Sum('votes')).order_by('-svotes'):
        constituency, number, votes = qs["constituency"], qs["count"], qs["svotes"]
        sconstituency = re.sub(" ", "_", constituency)
        lconstituency = '<a href="http://en.wikipedia.org/wiki/%s">WP: %s</a>' % (sconstituency, constituency)
        lconstituency = '<a href="C-%s">%s</a>' % (urllib.quote_plus(constituency), constituency)
        print r([lconstituency, str(number), str(votes)])
    print "</table>"

                                                                                                                             
def WriteCandidateYears():
    print '<table>'
    print "<tr><th>Candidate</th><th>Candidatures</th><th>Constituencies</th><th>Votes</th><tr>"
    for qs in DynElection.objects.values('candidate').annotate(count=Count('candidate'), constituencies=Count('constituency'), svotes=Sum('votes')).order_by('-count'):
        candidate, number, constituencies, votes = qs["candidate"], qs["count"], qs["constituencies"], qs["svotes"]
        scandidate = cgi.escape(candidate).encode("ascii", "xmlcharrefreplace")
        #sconstituency = re.sub(" ", "_", constituency)
        #lconstituency = '<a href="http://en.wikipedia.org/wiki/%s">WP: %s</a>' % (sconstituency, constituency)
        lcandidate = '<a href="A-%s">%s</a>' % (urllib.quote_plus(scandidate), scandidate)
        print r([lcandidate, str(number), str(constituencies), str(votes)])
    print "</table>"

    
def WriteElectionYears():
    print '<table>'
    print "<tr><th>Election</th><th>Constituencies</th><th>Candidates</th><th>Votes</th><tr>"
    # want it really to be Count('DISTINCT constituency')
    for qs in DynElection.objects.values('election').annotate(count=Count('election'), constituencies=Count('constituency'), svotes=Sum('votes')).order_by('-year'):
        election, number, nconstituencies, votes = qs["election"], qs["count"], qs["constituencies"], qs["svotes"]
        lelection = '<a href="E-%s">%s</a>' % (urllib.quote_plus(election), election)
        print r([lelection, str(nconstituencies), str(number), str(votes)])
    print "</table>"


def WritePartyVotes():
    print '<table id="vparty">'
    print "<tr><th>Party</th><th>Candidates</th><th>Votes</th><tr>"
    for qs in DynElection.objects.values('party').annotate(count=Count('party'), svotes=Sum('votes')):
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
        print "<h3>Total number of candidates and votes cast per constituency</h3>"
        print '<p>See <a href="party">count per party</a> or <a href="election">count per election</a> or <a href="candidate">count per candidate</a></p>'
        WriteConstituencyYears()
    elif tail == "election":
        print "<h3>Total number of candidates and votes cast per election</h3>"
        print '<p>See <a href="constituency">count per constituency</a> or <a href="party">count per party</a> or <a href="candidate">count per candidate</a></p>'
        WriteElectionYears()

    elif tail == "candidate":
        print "<h3>Total all number of candidates and votes cast per election</h3>"
        print '<p>See <a href="constituency">count per constituency</a> or <a href="party">count per party</a> or <a href="party">count per party</a></p>'
        WriteCandidateYears()

    elif tail[:2] == "P-":
        party = urllib.unquote_plus(tail[2:])
        WritePartyYears(party)
    elif tail[:2] == "C-":
        constituency = urllib.unquote_plus(tail[2:])
        WriteConstituency(constituency)
    elif tail[:2] == "E-":
         election = urllib.unquote_plus(tail[2:])
         WriteElection(election)
    elif tail[:2] == "A-":
         candidate = urllib.unquote_plus(tail[2:])
         WriteCandidate(candidate)
    else:
        if tail:
            print "<h2>tail: " + tail + "</h2>"
        print "<h3>Total number of candidates and votes fielded in all Parliamentary elections</h3>"
        print '<p>See <a href="constituency">count per constituency</a> or <a href="election">count per election</a> or <a href="candidate">count per candidate</a></p>'
        WritePartyVotes()
    print "</body>"
    print "</html>"
    

