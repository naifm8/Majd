from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('user_type', 'phone', 'organization', 'date_of_birth', 'bio', 'profile_picture')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff', 'is_active')
    list_filter = ('profile__user_type', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__organization')
    
    def get_user_type(self, obj):
        return obj.profile.user_type if hasattr(obj, 'profile') else 'N/A'
    get_user_type.short_description = 'User Type'
    get_user_type.admin_order_field = 'profile__user_type'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone', 'organization', 'created_at')
    list_filter = ('user_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'organization')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Contact Information', {
            'fields': ('phone', 'organization')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'bio', 'profile_picture')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
