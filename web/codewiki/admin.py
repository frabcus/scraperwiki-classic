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

def mark_featured(modeladmin, request, queryset):
    queryset.update(featured=True)
mark_featured.short_description = 'Mark selected items as featured'

def mark_unfeatured(modeladmin, request, queryset):
    queryset.update(featured=False)
mark_unfeatured.short_description = 'Mark selected items as unfeatured'

class CodeAdmin(admin.ModelAdmin):
    inlines = (UserCodeRoleInlines,)    
    readonly_fields = ('wiki_type','guid')

class ScraperAdmin(CodeAdmin):
    inlines = (UserCodeRoleInlines,)
    list_display = ('title', 'short_name', 'last_run', 'status', 'privacy_status')
    list_filter = ('status', 'last_run', 'privacy_status', 'featured',)
    search_fields = ('title', 'short_name')
    actions = [mark_featured, mark_unfeatured]

class ViewAdmin(CodeAdmin):
    list_filter = ('status', 'mime_type', 'privacy_status','featured',)
    search_fields = ('title', 'short_name')
    actions = [mark_featured, mark_unfeatured]

admin.site.register(Scraper, ScraperAdmin)
admin.site.register(View, ViewAdmin)
admin.site.register(ScraperMetadata)
admin.site.register(ScraperRunEvent)
