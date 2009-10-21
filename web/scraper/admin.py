import scraper.models
from django.contrib import admin

admin.site.register(scraper.models.Scraper)
admin.site.register(scraper.models.ScraperVersion)
admin.site.register(scraper.models.ScraperInvocation)
admin.site.register(scraper.models.ScraperException)
admin.site.register(scraper.models.UserScraperRole)
admin.site.register(scraper.models.PageAccess)
admin.site.register(scraper.models.ScraperRequest)
admin.site.register(scraper.models.scraperData)

