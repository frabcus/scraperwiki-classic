from web.codewiki.models import Scraper
from django.contrib.auth.models import User
from api.handlers.api_base import APIBase
from tagging.models import Tag
from piston.utils import rc
from codewiki import vc


class GetInfo(APIBase):
    required_arguments = ['name']
    
    def convert_history(self, commitentry):
        result = { 'version':commitentry['rev'], 'date':commitentry['date'] }
        try:    
            user = User.objects.get(pk=int(commitentry["userid"]))
            result['user'] = user.username
        except User.DoesNotExist: 
            pass
        lsession = commitentry['description'].split('|||')
        if len(lsession) == 2:
            result['session'] = lsession[0]
        return result

    def convert_run_event(self, runevent):
        result = { "runid":runevent.run_id, "run_started":runevent.run_started, 
                   "records_produced":runevent.records_produced, "pages_scraped":runevent.pages_scraped, 
                 }
        if runevent.run_ended:
            result['run_ended'] = runevent.run_ended
        if runevent.exception_message:
            result['exception_message'] = runevent.exception_message
        return result

    def value(self, request):
        scraper = self.get_scraper(request, wiki_type='')   # returns a Code object
        history_start_date = self.convert_date(request.GET.get('history_start_date', None))
            
        info = { }
        info['short_name']  = scraper.short_name
        info['language']    = scraper.language
        info['created']     = scraper.created_at
        info['title']       = scraper.title
        info['description'] = scraper.description
        info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
        if scraper.wiki_type == 'scraper':
            info['license']     = scraper.scraper.license
            info['last_run']    = scraper.scraper.last_run
            info['records']     = scraper.scraper.record_count
        
        try: 
            rev = int(request.GET.get('version', ''))
        except ValueError: 
            rev = None
            
        mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
        status = mercurialinterface.getstatus(scraper, rev)
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
            commitentries = mercurialinterface.getcommitlog(scraper)
            for commitentry in commitentries:
                if commitentry['date'] < history_start_date:
                    continue
                history.append(self.convert_history(commitentry))
            history.reverse()
            info['history'] = history
        
        if scraper.wiki_type == 'scraper':
            if history_start_date:
                runevents = scraper.scraper.scraperrunevent_set.filter(run_started__gt=history_start_date).order_by('-run_started')
            else:
                runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')[:2]
                
            info['runevents'] = [ ]
            for runevent in runevents:
                info['runevents'].append(self.convert_run_event(runevent))

        return [info,]      # a list with one element


class GetRunInfo(APIBase):
    required_arguments = ['name', 'runid']
    
    def value(self, request):
        scraper = self.get_scraper(request)
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
            runevent = scraper.scraper.scraperrunevent_set.get(run_id=runid)
            
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
            
        return [info,]      # a list with one element


class Search(APIBase):
    required_arguments = ['query']

    def value(self, request):
        query = request.GET.get('query', None) 
        result = [ ]  # list of dicts
        for scraper in Scraper.objects.search(query):
            result.append({'short_name':scraper.short_name, 'title':scraper.title, 'description':scraper.description, 'created':scraper.created_at})
        return result
