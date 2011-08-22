from django.contrib import admin
import whitelist.models

class WhitelistAdmin(admin.ModelAdmin):
    pass

admin.site.register(whitelist.models.Whitelist, WhitelistAdmin)

