from django.contrib import admin
from .models import Supplier

# Register your models here.
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    ordering = ['name']

admin.site.register(Supplier)