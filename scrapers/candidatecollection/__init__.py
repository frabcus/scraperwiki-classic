from codewiki.models import ScraperModule, DynElection, DynPartyCandidate
import re
        
# New file

def Scrape():
    pass

def DoesApply(reading):
    return False

def Parse(reading):
    return [ ]

def Collect():
    election, year = "next United Kingdom general election", "9999"
    source = "partywebpages"

    constituencymap = { }
    scrapermodule = ScraperModule.objects.get(modulename="labourcandidates")
    party = "Labour Party (UK)"
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        kvs = detection.contents()
        if not kvs:  # Hannah Cooper's
            continue
        kv = kvs[0]
        constituency = kv["constituency"]
        candidate = kv["name"]    
        constituencymap.setdefault(constituency, []).append((party, candidate, kv))

        
    scrapermodule = ScraperModule.objects.get(modulename="conservativecandidates")
    party = "Conservative Party (UK)"
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        kvs = detection.contents()
        kv = kvs[0]
        candidate = kv["name"]    
        constituency = kv.get("Prospective Parliamentary Candidate", "")
        if constituency:
            constituencymap.setdefault(constituency, []).append((party, candidate, kv))

    scrapermodule = ScraperModule.objects.get(modulename="libdemcandidates")
    party = "Liberal Democrats (UK)"
    for detection in scrapermodule.detection_set.filter(status="parsed"):
        kvs = detection.contents()
        kv = kvs[0]
        constituency = kv["constituency"]
        candidate = kv["name"]    
        constituencymap.setdefault(constituency, []).append((party, candidate, kv))
        
        
    DynPartyCandidate.objects.all().delete()
    DynElection.objects.filter(source=source).delete()
    for constituency, candidatelist in constituencymap.iteritems():
        print "CCC", constituency
        candidatemap = { }
        for party, candidate, kv in candidatelist:
            if party not in candidatemap:
                candidatemap[party] = (candidate, kv)
            else:
                assert candidatemap[party] == (candidate, kv)
        for party, (candidate, kv) in candidatemap.iteritems():
            candidaterow = DynElection(election=election, year=year, party=party, votes=0, constituency=constituency, candidate=candidate, source=source)
            candidaterow.save()
            partycandidate = DynPartyCandidate(candidaterow=candidaterow)
            partycandidate.email = kv.get("email", "")
            partycandidate.web = kv.get("web", "")
            partycandidate.phone = kv.get("phone", "")
            partycandidate.address = kv.get("address", "")
            partycandidate.urlsource = kv["url"]
            partycandidate.save()
            
rc = 0
def r(a):
    global rc
    if (rc % 2) == 1:
        return "<tr><td>%s</td></tr>" % "</td><td>".join(a)
    else:
        return '<tr><td class="grey">%s</td></tr>' % '</td><td class="grey">'.join(a)
    
            
        
def WriteHead():
    print "<html>"
    print "<head>"
    print '<style type="text/css">'
    print 'table {border-collapse: collapse; }'
    print 'td {border-left: thin black solid; border-right: thin black solid; }'
    print 'td.grey {background-color: #dcc; }'
    print 'th {background-color: black;  color: white; }'
    print '</style>'
    print '</head>'
    print '<body>'
        

def WriteSelectedCandidates():
    global rc
    print '<table>'
    print "<tr><th>Constituency</th><th>Party</th><th>Candidate</th><th>Email</th><th>Web</th><tr>"
    prevconstituency = ""    
    for qs in DynPartyCandidate.objects.all().order_by("candidaterow__constituency"):
        constituency, party, candidate = qs.candidaterow.constituency, qs.candidaterow.party, qs.candidaterow.candidate
        if (constituency != prevconstituency):
            rc += 1
            lconstituency = constituency
        else:
            lconstituency = " "
        
        lcandidate = '<a href="%s">%s</a>' % (qs.urlsource, candidate)
        lparty = { "Labour Party (UK)":"Labour", "Conservative Party (UK)":"Tory", "Liberal Democrats (UK)":"LibDem" }[party]
        lweb = qs.web and '<a href="%s">%s</a>' % (qs.web, re.sub("http://", "", qs.web)) or ""
        print r([lconstituency, lparty, lcandidate, qs.email, lweb])
        prevconstituency = constituency
                                                          
    print "</table>"
    
    
def Observe(tail):
    WriteHead()
    #if tail == "constituency":
    print "<h3>Selected Election Candidates</h3>"
    #print '<p>See <a href="constituency">count per constituency</a> or <a href="party">count per party</a> or <a href="candidate">count per candidate</a></p>'
    WriteSelectedCandidates()
    
        
