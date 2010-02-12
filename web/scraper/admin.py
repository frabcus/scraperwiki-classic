import scraper.models
import frontend.models
from django.contrib import admin


class ScraperInlines(admin.TabularInline):
  model = scraper.models.UserScraperRole
  extra = 1

class ScraperAdmin(admin.ModelAdmin):
    inlines = (ScraperInlines,)
    list_display = ('title', 'short_name', 'last_run', 'status','published',)
    list_filter = ('status', 'last_run', 'published',)

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('scraper', 'message_type', 'datetime', 'message_level',)
    list_filter = ('message_type', 'datetime', 'message_level',)

admin.site.register(scraper.models.Scraper, ScraperAdmin)
admin.site.register(scraper.models.ScraperHistory, HistoryAdmin)
