from codewiki.models import Scraper, ScraperMetadata, UserScraperRole, UserScraperEditing
from django.contrib import admin
from django.db import models

class UserScraperRoleInlines(admin.TabularInline):
    model = UserScraperRole
    extra = 1

class ScraperMetadataInlines(admin.TabularInline):
    model = ScraperMetadata
    max_num = 100
    extra = 1

class ScraperAdmin(admin.ModelAdmin):
    inlines = (UserScraperRoleInlines, ScraperMetadataInlines)
    list_display = ('title', 'short_name', 'last_run', 'status', 'published', 'deleted')
    list_filter = ('status', 'last_run', 'published',)

    def queryset(self, request):
        return Scraper.unfiltered

admin.site.register(Scraper, ScraperAdmin)


class ScraperMetadataAdmin(admin.ModelAdmin):
    pass

admin.site.register(ScraperMetadata, ScraperMetadataAdmin)


class UserScraperEditingAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserScraperEditing, UserScraperEditingAdmin)
