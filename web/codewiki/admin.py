from codewiki.models import Code, View, Scraper, ScraperMetadata, UserCodeRole, ScraperRunEvent
from django.contrib import admin
from django.db import models

class UserCodeRoleInlines(admin.TabularInline):
    model = UserCodeRole
    extra = 1

class ScraperMetadataInlines(admin.TabularInline):
    model = ScraperMetadata
    max_num = 100
    extra = 1

class ScraperRunEventInlines(admin.TabularInline):
    model = ScraperRunEvent
    extra = 0

class CodeAdmin(admin.ModelAdmin):
    inlines = (UserCodeRoleInlines,)    
    readonly_fields = ('wiki_type','guid')

    def queryset(self, request):
        return self.model.unfiltered.get_query_set()

class ScraperAdmin(CodeAdmin):
    inlines = (UserCodeRoleInlines,)
    list_display = ('title', 'short_name', 'last_run', 'status', 'published', 'deleted')
    list_filter = ('status', 'last_run', 'published', 'deleted')
    search_fields = ('title', 'short_name')

class ViewAdmin(CodeAdmin):
    list_filter = ('status', 'mime_type', 'published',)
    search_fields = ('title', 'short_name')


admin.site.register(Scraper, ScraperAdmin)
admin.site.register(View, ViewAdmin)
admin.site.register(ScraperMetadata)
admin.site.register(ScraperRunEvent)
