from django.db import models
from core.models import Product

# Create your models here.
class Inventory(models.Model):
    ''' Примерная моделя склада '''
    product = models.ForeignKey(
        Product,
        verbose_name='Продукт',
        on_delete=models.CASCADE
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    # Остальные поля...

    class Meta:
        verbose_name = 'склад'
        verbose_name_plural = 'Склады'
        ordering = ('-created_at',)

    # Заглушка
    def __str__(self):
        return f"{self.product.name}: {self.quantity}"