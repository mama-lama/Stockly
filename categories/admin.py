from django.contrib import admin
from .models import Category

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name']
    ordering = ['name']
