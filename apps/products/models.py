from django.db import models
from apps.categories.models import Category
from apps.suppliers.models import Supplier

class Product(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name='Название',
        unique=True
    )
    category_id = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Категория'
    )
    supplier_id = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Поставщик'
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Закупочная цена',
        help_text='Цена закупки в рублях'
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена продажи',
        help_text='розничная цена в рублях'
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Остаток на складе'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный',
        help_text='Отображать товар на складе'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'товары'
        ordering = ['name']

    def __str__(self):
        return self.name