from scraperutils import ScrapeURL
import re
import datetime
import sys
import os


def DoesApply(reading):
    return reading.scraper_tag == "wikipediadump" and re.search("\(UK Parliament constituency\)$", reading.name)


# parse out the {{ template | key=value | ... }} elements from a wikipedia page
def ParseTemplParams(bracket, templ, bracketclose):
    res = { }
    i = 0
    for param in templ:
        k, e, v = re.match("(?s)([^=]*)(=?)(.*)$", param).groups()
        if e:
            res[k.strip()] = v.strip()
        else:
            res[i] = k.strip()
        i += 1
    return res
        
def ParseTemplates(text):
    res = [ ]
    templstack = [ ]
    for tt in re.split("(\{\{\{|\}\}\}|\{\{|\}\}|\[\[|\]\]|\|)", text):
        if tt in ["{{{", "{{", "[["]:
            templstack.append([tt, [ [ ] ] ])
        elif templstack and tt in ["}}}", "}}", "]]"]:
            templstack[-1][1][-1] = "".join(templstack[-1][1][-1])
            templstack[-1].append(tt)
            if len(templstack) == 1:
                if templstack[-1][0] == "{{":
                    res.append(ParseTemplParams(templstack[-1][0], templstack[-1][1], templstack[-1][2]))
            else:
                templstack[-2][1][-1].append(templstack[-1][0])
                templstack[-2][1][-1].append("|".join(templstack[-1][1]))
                templstack[-2][1][-1].append(templstack[-1][2])
            del templstack[-1]
        elif tt == "|" and templstack:
            templstack[-1][1][-1] = "".join(templstack[-1][1][-1])
            templstack[-1][1].append([ ])
        elif templstack:
            templstack[-1][1][-1].append(tt)
    return res


def GetInfobox(title, templs):
    for templ in templs:
        if templ[0] == title:
            return templ
    return None


# this parsing will find out if the percentage reported per election agrees with the vote tally
def GetElectionCandidates(templs):
    res = { }
    candidatelist = [ ]
    electionnames = [ ]
    for templ in templs:
        if templ[0] == "Election box begin":
            electionname = re.search("title=\[\[(.*?)[\|\]]", templ["title"]).group(1)
            electionnames.append(electionname)
            candidatelist = [ templ["title"] ]
            res[templ["title"]] = candidatelist
        elif re.match("Election box candidate", templ[0]):
            candidatelist.append(templ)
        elif templ[0] == "Election box end":
            candidatelist = [ ]

    print electionnames


def Parse(reading):
    templs = ParseTemplates(reading.contents())
    for templ in templs:
        if templ[0] == "Election box begin":
            melectionname = re.search("\[\[(.*?)[\|\]]", templ["title"])
            electionname = melectionname and melectionname.group(1) or templ["title"]
            electionname = re.match("(.*?)\s*(\{\{.*|http://.*)?$", electionname).group(1)
            yield { "type":"election", "name":electionname }
        elif re.match("Election box candidate", templ[0]):
            svotes = re.sub("[,. ]", "", templ["votes"])
            if re.match("\d+$", svotes):
                votes = int(svotes)
            elif svotes in ["Unopposed", "unopposed", "Elected", "Co-opted", "''N/A''", "''(unopposed)''", "Unknown"]:
                votes = 1
            elif svotes == "":
                votes = 0
            elif svotes == "Defeated":
                votes = 0
            else:
                assert False, "Unparsed votes:" + str(templ)
                
            party = re.match("(.*?)\s*(\[?http://.*|{{|<!.*|<ref.*)?$", templ["party"]).group(1)
            mpartycat = re.match("(.*?)\[\[(.+?)[\|\]]", party)
            if mpartycat:
                party = mpartycat.group(1) + mpartycat.group(2)
            assert not re.search("\[|<", party), list(templ["party"])
                
            yield { "type":"candidate", "election":electionname, "constituency":reading.name, "votes":votes, "party":party }
        elif templ[0] == "Election box end":
            electionname = None
    
    

