from django.contrib import admin
from blog.models import Entry

class EntryAdmin(admin.ModelAdmin):
    fields = ['pub_date', 'author', 'headline', 'slug', 'body', 'summary']
    list_display = ('headline', 'pub_date', 'author')
    list_filter = ['pub_date']
    search_fields = ['headline']
    date_hierarchy = 'pub_date'

admin.site.register(Entry, EntryAdmin)
