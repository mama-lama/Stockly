from django.db import models

# Create your models here.
class BaseModel(models.Model):
    ''' Примерная базовая модель продукта '''
    created_at = models.DateTimeField(
        verbose_name='Добавлено',
        auto_created=True
        )
    updated_at = models.DateTimeField(
        verbose_name='Обновлено',
        auto_now=True
    )

    class Meta:
        abstract = True

class Product(BaseModel):
    ''' Примерная модель продукта '''
    name = models.CharField(
        verbose_name='Название',
        max_length=80
        )
    sku = models.CharField(
        verbose_name='Артикул',
        max_length=50,
        unique=True,
        )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
        )
    # Остальные поля


    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = "Продукты"
        ordering = ('name',)
    
    # Заглушка
    def __str__(self) -> str:
        return self.name