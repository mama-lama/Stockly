from django.db import models

# Create your models here.
class ExternalFactor(models.Model):
    date = models.DateField(unique=True, verbose_name='Дата')
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Температура (°C)",
        help_text="Среднесуточная температура"
    )
    is_holiday = models.BooleanField(
        default=False,
        verbose_name="Праздник",
        help_text="Государственный или религиозный праздник"
    )
    is_payday = models.BooleanField(
        default=False,
        verbose_name="День зарплаты",
        help_text="День выдачи заработной платы"
    )
    holiday_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Название праздника",
        help_text="Если праздник активен"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Примечания"
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
        verbose_name = "Внешний фактор"
        verbose_name_plural = "внешние факторы"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.temperature}°C"