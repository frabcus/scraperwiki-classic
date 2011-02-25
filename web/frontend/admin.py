from frontend.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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

class MessageAdmin(admin.ModelAdmin):
    pass

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')


admin.site.register(UserProfile)
admin.site.register(UserToUserRole)
admin.site.register(AlertTypes, AlertTypesAdmin)
admin.site.register(Alerts, AlertsAdmin)
admin.site.register(Message, MessageAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

