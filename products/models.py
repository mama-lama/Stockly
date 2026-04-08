from django.db import models
from categories.models import Category
from suppliers.models import Supplier
from users.models import User

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=120, verbose_name='Название', unique=True)
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
    
class InventoryOperation(models.Model):
    class OperationType(models.TextChoices):
        RECEIPT = 'receipt', 'Приход'
        SALE = 'sale', 'Продажа'
        WRITE_OFF = 'write_off', 'Списание'
        INVENTORY_ADJUSTMENT = 'inventory_adjustment', 'Корректировка'

    operation_type = models.CharField(
        max_length=50,
        choices=OperationType.choices,
        verbose_name='Тип операции',
        default='receipt'
        )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='operations',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество"
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Закупочная цена",
        help_text="Актуально для прихода"
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена продажи",
        help_text="Актуально для продажи"
    )
    operation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата операции"
    )
    note = models.TextField(
        blank=True,
        verbose_name="Примечание",
        help_text="Дополнительная информация об операции"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations',
        verbose_name="Кто выполнил"
    )

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
        ordering = ['-operation_date']

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.product.name} - {self.quantity} шт."
