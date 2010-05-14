from scraper.models import Scraper, ScraperMetadata, UserScraperRole
from django.contrib import admin
from django.db import models

class ScraperInlines(admin.TabularInline):
  model = UserScraperRole
  extra = 1

class ScraperAdmin(admin.ModelAdmin):
    inlines = (ScraperInlines,)
    list_display = ('title', 'short_name', 'last_run', 'status', 'published', 'deleted')
    list_filter = ('status', 'last_run', 'published',)

    def queryset(self, request):
        return Scraper.unfiltered

admin.site.register(Scraper, ScraperAdmin)

class ScraperMetadataAdmin(admin.ModelAdmin):
    pass

admin.site.register(ScraperMetadata, ScraperMetadataAdmin)
