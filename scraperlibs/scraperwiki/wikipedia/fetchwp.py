# encoding: utf-8
import os
import datetime
import connection


def getpage(title):
    """Load single wikipedia page"""
    conn = connection.Connection()
    c = conn.connect()
    if c.execute("SELECT text FROM `wikipediapages` WHERE title=%s", (title,)):
        return c.fetchone()[0]
    return None


def gettitles(ttag=None):
    """Load single wikipedia page"""
    conn = connection.Connection()
    c = conn.connect()
    if ttag:
        c.execute("SELECT title FROM `wikipediapages` WHERE ttag=%s", (ttag,))
    else:
        c.execute("SELECT title FROM `wikipediapages`")
    
    # must be a slicker way to do this
    res = [ ]
    while True:
        a = c.fetchone()
        if a:
            res.append(a[0])
        else:
            break
    return res
    
    


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

  