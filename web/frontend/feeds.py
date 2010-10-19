from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.core.exceptions import ObjectDoesNotExist
from codewiki.models import Code, Scraper, View
from tagging.utils import get_tag
from tagging.models import Tag, TaggedItem
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.conf import settings

current_site = Site.objects.get_current()
short_name = ""

class CommentsForCode(Feed):
    
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        short_name = bits[0]
        code_object = Code.objects.get(short_name__exact=short_name)
        if code_object:
            return code_object
        else:
            raise ObjectDoesNotExist
            
    def title(self, obj):
        return "ScraperWiki.com: comments on  '%s' | %s" % (obj.short_name, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()
        
    def item_link(self, obj):
        code_object = obj.content_object
        return "%s#%d" % (reverse('scraper_comments', args=[code_object.wiki_type, code_object.short_name]) , obj.id)

    def description(self, obj):
        return "Comments on '%s'" % obj.short_name

    def items(self, obj):
        return Comment.objects.for_model(obj).filter(is_public=True, is_removed=False).order_by('-submit_date')[:settings.RSS_ITEMS]
      
        
class LatestCodeObjectsByTag(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        tag = get_tag(bits[0])
        return tag
            
    def title(self, obj):
        return "ScraperWiki.com: items tagged with '%s' | %s" % (obj.name, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return reverse('single_tag', args=[obj.name])

    def item_link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return "Items recently created on ScraperWiki with tag '%s'" % obj.name

    def items(self, obj):
       scrapers = TaggedItem.objects.get_by_model(Scraper, obj)
       views = TaggedItem.objects.get_by_model(View, obj)
       return sorted(list(views) + list(scrapers), key=lambda x: x.created_at, reverse=True)[:settings.RSS_ITEMS]


class LatestCodeObjects(Feed):
    title = "Latest items | %s" % current_site.name
    link = "/browse"
    description = "All the latest scrapers and views added to ScraperWiki"

    def item_link(self, obj):
        return obj.get_absolute_url()
        
    def items(self):
        return Code.objects.filter(published=True).order_by('-created_at')[:settings.RSS_ITEMS]
        
        
class LatestCodeObjectsBySearchTerm(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        search_term = bits[0]
        search_term = search_term.strip()
        return search_term
            
    def title(self, obj):
        return "ScraperWiki.com: items matching '%s' | %s" % (obj, current_site.name)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return '/browse/tags/%s/' % obj

    def item_link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return "Items created with '%s' somewhere in title or tags" % obj

    def items(self, obj):
        code_objects = Code.objects.search(obj) 
        return code_objects[:settings.RSS_ITEMS]
        
