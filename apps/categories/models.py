from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название категории'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'категории'
        ordering = ['name']

    def __str__(self):
        return self.name