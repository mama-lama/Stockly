from django.contrib import admin
from .models import Product, InventoryOperation

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category_id', 'supplier_id',
        'purchase_price', 'sale_price', 'stock_quantity',
        'is_active', 'created_at'
    ]
    ordering = ['-created_at']

@admin.register(InventoryOperation)
class InventoryOperationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'operation_type', 'product',
        'quantity', 'purchase_price', 'sale_price',
        'operation_date', 'created_by'
    ]
    ordering = ['-operation_date']
    