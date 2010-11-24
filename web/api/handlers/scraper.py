from web.codewiki.models import Scraper
from api.handlers.api_base import APIBase
from tagging.models import Tag
from piston.utils import rc
from codewiki import vc



# history probably wants to be a separate call

class GetInfo(APIBase):
    required_arguments = ['name']
    
    def value(self, request):
        scraper = self.get_scraper(request)
            
        info = {}
        info['short_name']  = scraper.short_name
        info['language']    = scraper.language
        info['created']     = scraper.created_at
        info['title']       = scraper.title
        info['description'] = scraper.description
        info['tags']        = [tag.name for tag in Tag.objects.get_for_object(scraper)]
        info['license']     = scraper.license
        info['last_run']    = scraper.last_run
        info['records']     = scraper.record_count
        
        rev = request.GET.get('version') 
        mercurialinterface = vc.MercurialInterface(scraper.get_repo_path())
        status = mercurialinterface.getstatus(scraper, rev)
        
        info['code']        = status["code"]
        info['filemodifieddate'] = status['filemodifieddate']
        
        runevents = scraper.scraper.scraperrunevent_set.all().order_by('-run_started')[:1]
        if runevents:
            info['lastrunid'] = runevents[0].id

        return [info,]      # a list with one element


class Search(APIBase):
    required_arguments = ['query']

    def value(self, request):
        query = request.GET.get('query', None) 
        result = [ ]  # list of dicts
        for scraper in Scraper.objects.search(query):
            result.append({'short_name':scraper.short_name, 'title':scraper.title, 'description':scraper.description, 'created':scraper.created_at})
        return result
