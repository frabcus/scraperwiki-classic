import scraper.models
from django.contrib import admin


class ScraperAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_name', 'last_run', 'status',)
    list_filter = ('status', 'last_run')
    
admin.site.register(scraper.models.Scraper, ScraperAdmin)
admin.site.register(scraper.models.ScraperVersion)
admin.site.register(scraper.models.ScraperInvocation)
admin.site.register(scraper.models.ScraperException)
admin.site.register(scraper.models.UserScraperRole)
admin.site.register(scraper.models.PageAccess)
admin.site.register(scraper.models.ScraperRequest)
admin.site.register(scraper.models.scraperData)
