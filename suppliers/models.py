from django.db import models

# Create your models 
class Supplier(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название')
    contact_info = models.CharField(max_length=500, verbose_name='Контакты', help_text='Телефон, email, адрес, контактное лицо и т.д.')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлено')
    upload_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name