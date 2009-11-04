import scraper.models
from django.contrib import admin


class ScraperInlines(admin.TabularInline):
  model = scraper.models.UserScraperRole
  extra = 1

class ScraperAdmin(admin.ModelAdmin):
    inlines = (ScraperInlines,)
    list_display = ('title', 'short_name', 'last_run', 'status','published',)
    list_filter = ('status', 'last_run', 'published',)
    
admin.site.register(scraper.models.Scraper, ScraperAdmin)
# admin.site.register(scraper.models.ScraperVersion)
# admin.site.register(scraper.models.ScraperInvocation)
# admin.site.register(scraper.models.ScraperException)
# admin.site.register(scraper.models.UserScraperRole)
# admin.site.register(scraper.models.PageAccess)
# admin.site.register(scraper.models.ScraperRequest)
# admin.site.register(scraper.models.scraperData)
