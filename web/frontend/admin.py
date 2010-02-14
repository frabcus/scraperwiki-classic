from frontend.models import *
from django.contrib import admin

class AlertTypesAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'applies_to')


admin.site.register(UserProfile)
admin.site.register(UserToUserRole)
admin.site.register(AlertTypes, AlertTypesAdmin)

