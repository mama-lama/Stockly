from django.contrib import admin
from .models import Product, InventoryOperation

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'supplier_link', 
        'purchase_price', 'sale_price', 'profit_display',
        'stock_quantity', 'is_active'
    ]
    ordering = ['-created_at']

class InventoryOperationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'operation_type_colored', 'product_link', 
        'quantity', 'price_info', 'total_amount_display',
        'operation_date', 'created_by'
    ]
    ordering = ['-operation_date']

admin.site.register(Product)
admin.site.register(InventoryOperation)