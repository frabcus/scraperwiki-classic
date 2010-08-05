from codewiki.models import Scraper, ScraperMetadata, UserCodeRole, UserCodeEditing
from django.contrib import admin
from django.db import models

class UserCodeRoleInlines(admin.TabularInline):
    model = UserCodeRole
    extra = 1

class ScraperMetadataInlines(admin.TabularInline):
    model = ScraperMetadata
    max_num = 100
    extra = 1

class ScraperAdmin(admin.ModelAdmin):
    inlines = (UserCodeRoleInlines, ScraperMetadataInlines)
    list_display = ('title', 'short_name', 'last_run', 'status', 'published', 'deleted')
    list_filter = ('status', 'last_run', 'published',)

    def queryset(self, request):
        return Scraper.unfiltered

admin.site.register(Scraper, ScraperAdmin)


class ScraperMetadataAdmin(admin.ModelAdmin):
    pass

admin.site.register(ScraperMetadata, ScraperMetadataAdmin)


class UserCodeEditingAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserCodeEditing, UserCodeEditingAdmin)
