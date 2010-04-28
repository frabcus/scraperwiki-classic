from django.contrib import admin
import whitelist.models

class WhitelistAdmin(admin.ModelAdmin):
    pass

admin.site.register(whitelist.models.Whitelist, WhitelistAdmin)

# These need to be added to the database as whites

#.uk
#.police.uk
#.gov.uk
#.co.uk
#.com
#.eu
#.govt.nz
#.org
#.net
#.edu
