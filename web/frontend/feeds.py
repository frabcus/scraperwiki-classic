from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from scraper.models import Scraper
from tagging.utils import get_tag
from tagging.models import Tag, TaggedItem
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site

current_site = Site.objects.get_current()
scraper_name = ""

class CommentsForScraper(Feed):
    
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        scraper_name = bits[0]
        scraper = Scraper.objects.get(short_name__exact=scraper_name)
        if scraper: 
            global scraper_name 
            scraper_name = scraper.short_name
            return scraper
        else: 
            raise ObjectDoesNotExist
            
    def title(self, obj):
        return "ScraperWiki.com: comments on scraper '%s' | %s" % (obj.short_name, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return '/scrapers/%s/' % obj.short_name
        
    def item_link(self, item):
        return '/scrapers/show/%s/comments/#%s' % (scraper_name, item.id)

    def description(self, obj):
        return "Comments on scraper '%s'" % obj.short_name

    def items(self, obj):
        return Comment.objects.for_model(obj).filter(is_public=True, is_removed=False).order_by('-submit_date')[:15]  
      
        
class LatestScrapersByTag(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        tag = get_tag(bits[0])
        return tag
            
    def title(self, obj):
        return "ScraperWiki.com: Scrapers tagged with '%s' | %s" % (obj.name, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return '/scrapers/tags/%s/' % obj.name
        
    def item_link(self, item):
        return '/scrapers/%s/' % item.short_name

    def description(self, obj):
        return "Scrapers recently published on ScraperWiki with tag '%s'" % obj.name

    def items(self, obj):
       scrapers = Scraper.objects.filter(published=True)    
       queryset = TaggedItem.objects.get_by_model(scrapers, obj)
       return queryset.order_by('-created_at')[:30]
       
       
class LatestScrapers(Feed):
    title = "Latest scrapers | %s" % current_site.name
    link = "/scrapers/list"
    description = "All the latest scrapers added to ScraperWiki"
   
        
    def item_link(self, item):
        return '/scrapers/%s/' % item.short_name
        
    def items(self):
        return Scraper.objects.filter(published=True).order_by('-created_at')[:10]
        
        
class LatestScrapersBySearchTerm(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        search_term = bits[0]
        search_term = search_term.strip()
        return search_term
            
    def title(self, obj):
        return "ScraperWiki.com: Scrapers matching '%s' | %s" % (obj, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return '/scrapers/tags/%s/' % obj
        
    def item_link(self, item):
        return '/scrapers/%s/' % item.short_name

    def description(self, obj):
        return "Scrapers published with '%s' somewhere in title or tags" % obj

    def items(self, obj):
        scrapers = Scraper.objects.filter(title__icontains=obj, published=True) 
        tag = Tag.objects.filter(name__icontains=obj)
        if tag: 
          qs = TaggedItem.objects.get_by_model(Scraper, tag)
          scrapers = scrapers | qs
        scrapers = scrapers.filter(published=True).order_by('-created_at')
        return scrapers[:10]
        
