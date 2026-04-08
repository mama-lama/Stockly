from django.contrib import admin
from .models import ExternalFactor

# Register your models here.
@admin.register(ExternalFactor)
class ExternalFactorAdmin(admin.ModelAdmin):
    list_display = [
        'date', 
        'temperature',
        'is_holiday',
        'is_payday',
        'holiday_name',
        'notes',
        'created_at'
    ]
    ordering = ['-date']
