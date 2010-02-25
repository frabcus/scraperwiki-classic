from frontend.models import *
from django.contrib import admin

# Don't put AlertTypes in admin, as we need to control them via fixtures only
class AlertTypesAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'name', 'label', 'applies_to')

class AlertsAdmin(admin.ModelAdmin):
    list_display = (
        'content_object',
        'message_type',
        'datetime',
        'message_level',)
    list_filter = ('message_type', 'datetime', 'message_level',)



admin.site.register(UserProfile)
admin.site.register(UserToUserRole)
admin.site.register(AlertTypes, AlertTypesAdmin)
admin.site.register(Alerts, AlertsAdmin)