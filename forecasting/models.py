from django.db import models
from core.models import Product

# Create your models here.
class Forecast(models.Model):
    ''' Примерная модель прогноза '''
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        on_delete=models.CASCADE
        )
    forecast_date = models.DateField(
        verbose_name='Дата прогноза'
        )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
        )
    # Остальные поля
    
    class Meta:
        verbose_name = 'прогноз'
        verbose_name_plural = 'Прогнозы'
        ordering = ('-forecast_date',)

    # Заглушка
    def __str__(self):
        return f'Прогноз для {self.product.name} на {self.forecast_date}'