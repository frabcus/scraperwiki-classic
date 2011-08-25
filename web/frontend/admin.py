from frontend.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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
admin.site.register(Message, MessageAdmin)
admin.site.register(DataEnquiry, DataEnquiryAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

