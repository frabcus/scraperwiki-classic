import sys
import difflib
import re
sys.path.append('../../web')

import os
from django.conf import settings

import datetime
import time
import codecs
import mercurial
import mercurial.ui
import mercurial.hg


# The documentation and help strings for this Mercurial interface is inadequate
# The best bet is to look directly at the source code to work out what attributes exist
# (although can't be done for repo.commit as this is in hgext.mq, which I can't find)
# mercurial.commands module is mostly a wrapper on the functionality of the repo object

class MercurialInterface:
    def __init__(self, repo_path):
        self.ui = mercurial.ui.ui()
        self.ui.setconfig('ui', 'interactive', 'off')
        self.ui.setconfig('ui', 'verbose', 'on')
        self.repopath = os.path.normpath(os.path.abspath(repo_path))  # probably to handle windows values
        
        # danger with member copy of repo as not sure if it updates with commits
        # (definitely doesn't update if commit is done against a second repo object)
        self.repo = mercurial.hg.repository(self.ui, self.repopath)    
    
    
    def save(self, scraper, code):
        scraperfolder = os.path.join(self.repopath, scraper.short_name)
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        scraperpath = os.path.join(scraperfolder, "__init__.py")
        
        if not os.path.exists(scraperfolder):
            os.makedirs(scraperfolder)
        
        fout = codecs.open(scraperpath, mode='w', encoding='utf-8')
        fout.write(code)
        fout.close()

    
    # need to dig into the commit command to find the rev
    def commit(self, scraper, message="changed", user="unknown"): 
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        scraperpath = os.path.join(self.repopath, scraper.short_name, "__init__.py")
        
        # add into mercurial (must be relative to repopath)
        if scraperfile not in self.repo.dirstate:
            self.repo.add([scraperfile])   
        
        if message is None:
            message = "changed"

        node = self.repo.commit(message, str(user.pk))  
        if not node:
            return None
        return self.repo.changelog.rev(node)

    
    # this function possibly in wrong place (which makes the imports awkward)
    def updatecommitalertsrev(self, rev):
        from codewiki.models import Code, CodeCommitEvent
        from frontend.models import Alerts
        from django.contrib.auth.models import User

        
        # discard all alerts and commit events for this revision (made complex due to the indirection through CodeCommitEvent for a integer)
        for codecommitevent in CodeCommitEvent.objects.filter(revision=rev):
            for alert in Alerts.objects.filter(event_type=codecommitevent.content_type(), event_id=codecommitevent.id):
                alert.delete()
            codecommitevent.delete()
        
        warnings = [ ]
        
        ctx = self.repo[rev]
        commitentry = self.getctxrevisionsummary(ctx)
        
        user = None
        try:    
            user = User.objects.get(id=int(commitentry["userid"]))
        except: 
            warnings.append("Unmatched userid: %s" % commitentry.get("userid"))
        
        # there should actually be only one file in this batch, if everything is going right
        if len(ctx.files()) != 1:
            warnings.append("More than one file in rev: %s" % ctx.files())
        for scraperfile in ctx.files():
            mscraper = re.match("(.*?)/__init__.py", scraperfile)
            if not mscraper:
                warnings.append("unrecognized scraperfile: %s" % scraperfile)
                continue
            scrapers = Code.objects.filter(short_name=mscraper.group(1))
            if len(scrapers) != 1:
                warnings.append("scraperfile unmatched to scraper: %s" % scraperfile)
                continue
            scraper = scrapers[0]
    
            # yes, the allocation of information (eg the date) between the Alert and the CodeCommitEvent looks in fact arbitrary.  
            codecommitevent = CodeCommitEvent(revision=rev)
            codecommitevent.save()
            
            # extract earliesteditor from commit message
            description = commitentry["description"]
            earliesteditor = ''
            mearliesteditor = re.match("(.+?)\|\|\|", commitentry["description"])
            if mearliesteditor:
                earliesteditor = mearliesteditor.group(1)
                description = description[mearliesteditor.end(0):]
            
            alert = Alerts(content_object=scraper, message_type='commit', message_value=description, historicalgroup=earliesteditor, 
                           user=user, event_object=codecommitevent, datetime=commitentry["date"])
            alert.save()
        return warnings
    
    
    # delete and rebuild all the CodeCommitEvents and related alerts 
    # to make migration easy (and question whether these objects really need to exist)
    def updateallcommitalerts(self):
        from codewiki.models import Scraper, CodeCommitEvent
        from frontend.models import Alerts
        from django.contrib.auth.models import User
        
        # remove all alerts and commit events 
        Alerts.objects.filter(message_type='commit').delete()
        CodeCommitEvent.objects.all().delete()
        
        for rev in self.repo:
            warnings = self.updatecommitalertsrev(rev)
            if warnings:
                print "updateallcommitalerts warnings", warnings

    
    def getctxrevisionsummary(self, ctx):
        data = { "rev":ctx.rev(), "userid":ctx.user(), "description":ctx.description() }
        epochtime, offset = ctx.date()
        ltime = time.localtime(epochtime)
        data["date"] = datetime.datetime(*ltime[:7])
        data["date_isDST"] = ltime[-1]
        data["files"] = ctx.files()
        return data
            
    
    def getreversion(self, rev):
        ctx = self.repo[rev]
        result = self.getctxrevisionsummary(ctx)
        result["text"] = { }
        for f in ctx.files():
            ftx = ctx.filectx(f)
            result["text"][f] = ftx.data()
        return result
        
	            
    def getcommitlog(self, scraper):
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        result = [ ]
        
        for rev in self.repo:
            ctx = self.repo[rev]
            if scraperfile in ctx.files():
                result.append(self.getctxrevisionsummary(ctx))
        return result
            
    def getfilestatus(self, scraper):
        status = { }
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        scraperpath = os.path.join(self.repopath, scraperfile)
        
        lmtime = time.localtime(os.stat(scraperpath).st_mtime)
        status["filemodifieddate"] = datetime.datetime(*lmtime[:7])
        modified, added, removed, deleted, unknown, ignored, clean = self.repo.status()
        
        #print "sssss", (modified, added, removed, deleted, unknown, ignored, clean)
        status["ismodified"] = (scraperfile in modified)
        status["isadded"] = (scraperfile in added)
        
        return status


    def getstatus(self, scraper, rev=None):
        status = { }
        scraperfile = os.path.join(scraper.short_name, "__init__.py")
        scraperpath = os.path.join(self.repopath, scraperfile)

        # adjacent commit informations
        if rev != None:
            commitlog = self.getcommitlog(scraper)
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
            status.update(self.getfilestatus(scraper))

        if "prevcommit" in status:
            reversion = self.getreversion(status["prevcommit"]["rev"])
            prevcode = reversion["text"].get(scraperfile)
            if prevcode and status["code"]:
                status["matchlines"] = list(DiffLineSequenceChanges(prevcode, status["code"]))
        
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
        return (0, 0, 0, 0)  
    
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
    return (matchlinesfront, matchcharsfront, matchlinesbackb, matchcharsbackb)
      #, matchingcblocksback, (len(a[matchlinesbacka]) -
      #  matchingcblocksback[-2][2], len(b[matchlinesbackb]) - 
      #  matchingcblocksback[-2][2]))




