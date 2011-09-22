from frontend.models import *
from codewiki.models import UserUserRole, Vault
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

class UserUserRoleInlines(admin.TabularInline):
    model = UserUserRole
    fk_name = 'user'
    extra = 0

class VaultInlines(admin.StackedInline):
    model = Vault
    extra = 0
 
class UserProfileInlines(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'profile_name', 'vault_count', 'is_active', 'is_staff','is_beta_user', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser')


    def is_beta_user(self, obj):
        return obj.get_profile().beta_user

    def vault_count(self, obj):
        return obj.vaults.count()
        
    def profile_name(self, obj):
        return obj.get_profile().name

    inlines = [UserProfileStack, UserUserRoleInlines, VaultInlines]

admin.site.register(Message, MessageAdmin)
admin.site.register(DataEnquiry, DataEnquiryAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

