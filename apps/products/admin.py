from django.contrib import admin

from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'supplier_link', 
        'purchase_price', 'sale_price', 'profit_display',
        'stock_quantity', 'is_active'
    ]
    ordering = ['-created_at']

admin.site.register(Product)