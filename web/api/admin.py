from api.models import api_key
from django.contrib import admin

class ApiAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'active',)
    list_filter = ('active', 'user',)

admin.site.register(api_key, ApiAdmin)
