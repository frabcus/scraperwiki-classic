from models import Scraper
from django.contrib import admin

class ScraperAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_name', 'last_run', 'status',)
    list_filter = ('status', 'last_run')
    
admin.site.register(Scraper, ScraperAdmin)
