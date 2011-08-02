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

class DataEnquiryAdmin(admin.ModelAdmin):
    pass


class UserProfileStack(admin.StackedInline):
    model = UserProfile

    fk_name = 'user'
    max_num = 1
    extra = 0
    
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')

    inlines = [UserProfileStack, ]

class UserProfileAdmin(admin.ModelAdmin):
    """  
    Should quite possibly be inline in the user object.
    """
    list_display = ('username','fullname', 'active', 'staff_status')
    list_filter = ('beta_user',)
    
    def username(self, obj):
      return obj.user.username
      
    def active(self, obj):
      return obj.user.is_active      
      
    def staff_status(self, obj):
      return obj.user.is_staff            
      
    def fullname(self, obj):
      return obj.user.get_full_name()      
      
      
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserToUserRole)
admin.site.register(AlertTypes, AlertTypesAdmin)
admin.site.register(Alerts, AlertsAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(DataEnquiry, DataEnquiryAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

