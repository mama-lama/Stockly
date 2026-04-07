from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('created_at',)}),
    )
    list_display = ['username', 'email', 'is_staff', 'created_at']

admin.site.register(User, CustomUserAdmin)