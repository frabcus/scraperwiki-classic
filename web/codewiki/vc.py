import sys
import difflib
import re

import os
from django.conf import settings

import datetime
import time
import codecs
import mercurial
import mercurial.ui
import mercurial.hg

from django.contrib.auth.models import User



# The documentation and help strings for this Mercurial interface is inadequate
# The best bet is to look directly at the source code to work out what attributes exist
# (although can't be done for repo.commit as this is in hgext.mq, which I can't find)
# mercurial.commands module is mostly a wrapper on the functionality of the repo object

# this class only used in codewiki/models/code.py
class MercurialInterface:
    def __init__(self, repo_path, cloned_from_path=None):
        self.ui = mercurial.ui.ui()
        self.ui.setconfig('ui', 'interactive', 'off')
        self.ui.setconfig('ui', 'verbose', 'off')
        self.repopath = os.path.normpath(os.path.abspath(repo_path))  # (hg possibly over-sensitive to back-slashes)
            
        if not os.path.exists(self.repopath) and cloned_from_path:
            self.cloned_from_path = os.path.normpath(os.path.abspath(cloned_from_path))  # (hg possibly over-sensitive to back-slashes)
            mercurial.hg.clone(self.ui, str(self.cloned_from_path), str(self.repopath))

            # danger with member copy of repo as not sure if it updates with commits
            # (definitely doesn't update if commit is done against a second repo object)
        self.repo = mercurial.hg.repository(self.ui, self.repopath, create=not os.path.exists(self.repopath))    
    
    
    def savecode(self, code):
        assert os.path.exists(self.repopath)
        scraperpath = os.path.join(self.repopath, "code")   # 'code' is the default name for the only file in each repo (for now)
        fout = codecs.open(scraperpath, mode='w', encoding='utf-8')
        fout.write(code)
        fout.close()

    
    # need to dig into the commit command to find the rev
    def commit(self, message, user): 
        assert os.path.exists(os.path.join(self.repopath, "code"))
        if "code" not in self.repo.dirstate:
            self.repo.add(["code"])   
        
        if message is None:
            message = "changed"

        node = self.repo.commit(message, user.username)
        if not node:
            return None
        return self.repo.changelog.rev(node)
        
    
    def getctxrevisionsummary(self, ctx):
        description = ctx.description()
        data = { "rev":ctx.rev(), "userval":ctx.user(), "description":description }
        data['editingsession'] = description.split('|||')[0]
        epochtime, offset = ctx.date()
        ltime = time.localtime(epochtime)
        data["date"] = datetime.datetime(*ltime[:7])
        data["date_isDST"] = ltime[-1]
        data["files"] = ctx.files()

        luser = User.objects.filter(username=data["userval"])
        if luser:
            data["user"] = luser[0]
        elif re.match("\d+$", data["userval"]):    # older ones are by pk rather than username
            luser = User.objects.filter(pk=int(data["userval"]))
            if luser:
                data["user"] = luser[0]
        
        return data


            # this function is used externally when getting a second version to diff against
    def getreversion(self, rev):
        ctx = self.repo[rev]
        result = self.getctxrevisionsummary(ctx)
        result["text"] = { }
        for f in ctx.files():
            ftx = ctx.filectx(f)
            result["text"][f] = ftx.data()
        return result
        
	            
    def getcommitlog(self):
        result = [ ]
        for rev in self.repo:
            ctx = self.repo[rev]
            if "code" in ctx.files():   # could get both if changes in description
                result.append(self.getctxrevisionsummary(ctx))
        return result
        
    
    def getfilestatus(self):
        status = { }
        scraperpath = os.path.join(self.repopath, "code")
        
        lmtime = time.localtime(os.stat(scraperpath).st_mtime)
        status["filemodifieddate"] = datetime.datetime(*lmtime[:7])
        modified, added, removed, deleted, unknown, ignored, clean = self.repo.status()
        
        #print "sssss", (modified, added, removed, deleted, unknown, ignored, clean)
        status["ismodified"] = ("code" in modified)
        status["isadded"] = ("code" in added)  # false if actually committed (ie true means we're in an awkward state)
        return status
        

    def getstatus(self, rev=None):
        status = { }
        scraperfile = "code"
        scraperpath = os.path.join(self.repopath, "code")
        
        # adjacent commit informations
        if rev != None:
            commitlog = self.getcommitlog()
            if commitlog:
                irev = len(commitlog)
                if rev < 0:
                    irev = len(commitlog) + (rev+1)
                else:
                    for lirev in range(len(commitlog)):
                        if commitlog[lirev]["rev"] == rev:
                            irev = lirev
                            break

                if 0 <= irev < len(commitlog):
                    status["currcommit"] = commitlog[irev]
                if 0 <= irev - 1 < len(commitlog):
                    status["prevcommit"] = commitlog[irev - 1]
                if 0 <= irev + 1 < len(commitlog):
                    status["nextcommit"] = commitlog[irev + 1]
        
        # fetch code from reversion or the file
        if "currcommit" in status:
            reversion = self.getreversion(status["currcommit"]["rev"])
            status["code"] = reversion["text"].get(scraperfile)
        
        # get information about the saved file (which we will if there's no current revision selected -- eg when rev in [-1, None]
        else:
            fin = codecs.open(scraperpath, mode='rU', encoding='utf-8')
            status["code"] = fin.read()
            fin.close()
            status.update(self.getfilestatus()) # keys: filemodifieddate, isadded, ismodified
        
        status['scraperfile'] = scraperfile
        return status




def DiffLineSequenceChanges(oldcode, newcode):
    """
    Find the range in the code so we can show a watching user who has clicked
    on refresh what has just been edited this involves doing sequence matching
    on the lines, and then sequence matching on the first and last lines that
    differ    
    """
    
    a = oldcode.splitlines()
    b = newcode.splitlines()
    sqm = difflib.SequenceMatcher(None, a, b)
    matchingblocks = sqm.get_matching_blocks()  # [ (i, j, n) ] where  a[i:i+n] == b[j:j+n].
    assert matchingblocks[-1] == (len(a), len(b), 0)
    matchlinesfront = (matchingblocks[0][:2] == (0, 0) and matchingblocks[0][2] or 0)
    
    if (len(matchingblocks) >= 2) and (matchingblocks[-2][:2] == (len(a) - matchingblocks[-2][2], len(b) - matchingblocks[-2][2])):
        matchlinesback = matchingblocks[-2][2]
    else:
        matchlinesback = 0
    
    matchlinesbacka = len(a) - matchlinesback - 1
    matchlinesbackb = len(b) - matchlinesback - 1

    # no difference case
    if matchlinesbackb == -1:
        return None  
    
    # lines have been cleanly deleted, so highlight first character where it happens
    if matchlinesbackb < matchlinesfront:
        assert matchlinesbackb == matchlinesfront - 1
        return (matchlinesfront, 0, matchlinesfront, 1)
    
    # find the sequence start in first line that's different
    afront = matchlinesfront < len(a) and a[matchlinesfront] or ""
    bfront = matchlinesfront < len(b) and b[matchlinesfront] or ""
    sqmfront = difflib.SequenceMatcher(None, afront, bfront)
    matchingcblocksfront = sqmfront.get_matching_blocks()  # [ (i, j, n) ] where  a[i:i+n] == b[j:j+n].
    matchcharsfront = (matchingcblocksfront[0][:2] == (0, 0) and matchingcblocksfront[0][2] or 0)
    
    # find sequence end in last line that's different
    if (matchlinesbacka, matchlinesbackb) != (matchlinesfront, matchlinesfront):
        sqmback = difflib.SequenceMatcher(None, a[matchlinesbacka], b[matchlinesbackb])
        matchingcblocksback = sqmback.get_matching_blocks()  
    else:
        matchingcblocksback = matchingcblocksfront
    
    if (len(matchingcblocksback) >= 2) and (matchingcblocksback[-2][:2] == (len(a[matchlinesbacka]) - matchingcblocksback[-2][2], len(b[matchlinesbackb]) - matchingcblocksback[-2][2])):
        matchcharsback = matchingcblocksback[-2][2]
    else:
        matchcharsback = 0
    matchcharsbackb = len(b[matchlinesbackb]) - matchcharsback
    return { "startline":matchlinesfront, "startoffset":matchcharsfront, "endline":matchlinesbackb, "endoffset":matchcharsbackb }




