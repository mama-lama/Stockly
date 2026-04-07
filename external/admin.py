from django.contrib import admin
from .models import ExternalFactor

# Register your models here.
class ExternalFactorAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'temperature_colored', 'is_holiday_badge', 
        'is_payday_badge', 'is_weekend', 'season', 
        'impact_score_display', 'weather_condition'
    ]
    ordering = ['-date']

admin.site.register(ExternalFactor)