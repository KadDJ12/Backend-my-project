from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin as userAdmin

class CustomUserAdmin(userAdmin):
    model = CustomUser
    list_display = ('phone', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name')
    ordering = ('phone',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role & Permissions', {
        'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
        'classes': ('wide',),
        'fields': ('phone', 'first_name', 'last_name',
        'role', 'password1', 'password2'),
    }),
)
admin.site.register(CustomUser, CustomUserAdmin)