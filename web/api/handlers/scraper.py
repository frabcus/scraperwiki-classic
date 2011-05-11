from web.codewiki.models import Code, ScraperRunEvent, scraper_search_query
from django.contrib.auth.models import User
from frontend.models import UserToUserRole
from api.handlers.api_base import APIBase
from tagging.models import Tag
from piston.utils import rc
from codewiki.managers.datastore import DataStore


class GetInfo(APIBase):
    def convert_history(self, commitentry):
        result = { 'version':commitentry['rev'], 'date':commitentry['date'] }
        if 'user' in commitentry:
            result["user"] = commitentry['user'].username
        lsession = commitentry['description'].split('|||')
        if len(lsession) == 2:
            result['session'] = lsession[0]
        return result

    def convert_run_event(self, runevent):
        result = { "runid":runevent.run_id, "run_started":runevent.run_started, 
                   "records_produced":runevent.records_produced, "pages_scraped":runevent.pages_scraped, 
                   "still_running":(runevent.pid != -1), "last_update":runevent.run_ended, 
                 }
        if runevent.exception_message:
            result['exception_message'] = runevent.exception_message
        return result

    def value(self, request):
        scraper = self.getscraperorrccode(request, request.GET.get('name'), "apiscraperinfo")
        history_start_date = self.convert_date(request.GET.get('history_start_date', None))
        quietfields        = request.GET.get('quietfields', "").split("|")
            
        info = { }
        info['short_name']  = scraper.short_name
        info['language']    = scraper.language
        info['created']     = scraper.created_at
        
        info['title']       = scraper.title
        info['description'] = scraper.description
        info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
        info['wiki_type']   = scraper.wiki_type
        info['privacy_status'] = scraper.privacy_status
        if scraper.wiki_type == 'scraper':
            info['license']     = scraper.scraper.license
            info['records']     = scraper.scraper.record_count  # old style datastore
            
            if 'datasummary' not in quietfields:
                dataproxy = DataStore(scraper.short_name)
                sqlitedata = dataproxy.request({"maincommand":"sqlitecommand", "command":"datasummary", "val1":0, "val2":None})
                if sqlitedata and type(sqlitedata) not in [str, unicode]:
                    info['datasummary'] = sqlitedata
        
        if 'userroles' not in quietfields:
            info['userroles']   = { }
            for ucrole in scraper.usercoderole_set.all():
                if ucrole.role not in info['userroles']:
                    info['userroles'][ucrole.role] = [ ]
                info['userroles'][ucrole.role].append(ucrole.user.username)
        print info            
                
        try: 
            rev = int(request.GET.get('version', ''))
        except ValueError: 
            rev = None
            
        status = scraper.get_vcs_status(rev)
        if 'code' not in quietfields:
            info['code']        = status["code"]
        
        for committag in ["currcommit", "prevcommit", "nextcommit"]:
            if committag in status:
                info[committag] = self.convert_history(status[committag])
        
        if "currcommit" not in status and "prevcommit" in status and not status["ismodified"]:
            if 'filemodifieddate' in status:
                info["modifiedcommitdifference"] = status["filemodifieddate"] - status["prevcommit"]["date"]
                info['filemodifieddate'] = status['filemodifieddate']

        if history_start_date:
            history = [ ]
            commitentries = scraper.get_commit_log()
            for commitentry in commitentries:
                if commitentry['date'] < history_start_date:
                    continue
                history.append(self.convert_history(commitentry))
            history.reverse()
            info['history'] = history
        
        if scraper.wiki_type == 'scraper' and 'runevents' not in quietfields:
            if history_start_date:
                runevents = scraper.scraper.scraperrunevent_set.filter(run_ended__gte=history_start_date).order_by('-run_started')
            else:
                runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')[:2]
                
            info['runevents'] = [ ]
            for runevent in runevents:
                info['runevents'].append(self.convert_run_event(runevent))

        return [info]      # a list with one element


class GetRunInfo(APIBase):
    
    def value(self, request):
        scraper = self.getscraperorrccode(request, request.GET.get('name'), "apiscraperruninfo")
        runid = request.GET.get('runid', '-1')
        runevent = None
        if runid[0] == '-':   # allow for negative indexes to get to recent runs
            try:
                i = -int(runid)
                runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')
                if i < len(runevents):
                    runevent = runevents[i]
            except ValueError:
                pass
        if not runevent:
            try:
                runevent = scraper.scraper.scraperrunevent_set.get(run_id=runid)
            except ScraperRunEvent.DoesNotExist:
                error_response = rc.NOT_FOUND
                error_response.write(": Run object not found")
                return error_response

        info = { "runid":runevent.run_id, "run_started":runevent.run_started, 
                 "records_produced":runevent.records_produced, "pages_scraped":runevent.pages_scraped, 
               }
        if runevent.run_ended:
            info['run_ended'] = runevent.run_ended
        if runevent.exception_message:
            info['exception_message'] = runevent.exception_message
        
        info['output'] = runevent.output
        if runevent.first_url_scraped:
            info['first_url_scraped'] = runevent.first_url_scraped
        
        domainsscraped = [ ]
        for domainscrape in runevent.domainscrape_set.all():
            domainsscraped.append({'domain':domainscrape.domain, 'bytes':domainscrape.bytes_scraped, 'pages':domainscrape.pages_scraped})
        if domainsscraped:
            info['domainsscraped'] = domainsscraped
            
        return [info]      # a list with one element


class Search(APIBase):
    def value(self, request):
        query = request.GET.get('query', None) 
        if not query:
            query = request.GET.get('searchquery', None) 
        maxrows = 5
        try:   maxrows = int(request.GET.get('maxrows', ""))
        except ValueError: pass
        result = [ ]  # list of dicts
        scrapers = scraper_search_query(user=None, query=query)
        for scraper in scrapers[:maxrows]:
            res = {'short_name':scraper.short_name }
            res['title'] = scraper.title
            owners = scraper.userrolemap()["owner"]
            if owners:
                owner = owners[0]
                ownername = owner.get_profile().name
                if not ownername:
                    ownername = owner.username
                if ownername:
                    res['title'] = "%s / %s" % (ownername, scraper.title)
            res['description'] = scraper.description
            res['created'] = scraper.created_at
            res['privacy_status'] = scraper.privacy_status
            result.append(res)
        return result


class GetUserInfo(APIBase):
            # could be authorized with "apiuserinfo", but no scraper associated to authorize this
    def value(self, request):
        username = request.GET.get('username', "") 
        users = User.objects.filter(username=username)
        result = [ ]
        for user in users:  # list of users is normally 1
            info = { "username":user.username, "profilename":user.get_profile().name, "datejoined":user.date_joined }
            info['coderoles'] = { }
            for ucrole in user.usercoderole_set.exclude(code__privacy_status="deleted").exclude(code__privacy_status="private"):
                if ucrole.role not in info['coderoles']:
                    info['coderoles'][ucrole.role] = [ ]
                info['coderoles'][ucrole.role].append(ucrole.code.short_name)

            info['fromuserroles'] = { }
            for fromuserrole in user.from_user.all():
                if fromuserrole.role not in info['fromuserroles']:
                    info['fromuserroles'][fromuserrole.role] = [ ]
                info['fromuserroles'][fromuserrole.role].append(fromuserrole.from_user.username)
            
            info['touserroles'] = { }
            for touserrole in user.to_user.all():
                if touserrole.role not in info['touserroles']:
                    info['touserroles'][touserrole.role] = [ ]
                info['touserroles'][touserrole.role].append(touserrole.to_user.username)
            
            result.append(info)
        return result
