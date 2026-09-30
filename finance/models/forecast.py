from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ForecastType(models.TextChoices):
    """Типы прогнозов."""
    INCOME = "income", _("Доход")
    EXPENSE = "expense", _("Расход")
    SALARY = "salary", _("Зарплата")
    PROFIT = "profit", _("Прибыль")

class Forecast(models.Model):
    """
    Прогноз доходов/расходов на будущий период.
    """
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="forecasts",
        verbose_name="Компания",
    )
    forecast_type = models.CharField(
        max_length=20,
        choices=ForecastType.choices,
        verbose_name="Тип прогноза",
    )
    period_month = models.PositiveIntegerField(
        verbose_name="Месяц прогноза",
        help_text="Номер месяца (1-12)",
    )
    period_year = models.PositiveIntegerField(
        verbose_name="Год прогноза",
    )
    estimated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Прогнозируемая сумма",
    )
    actual_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Фактическая сумма",
        help_text="Заполняется после завершения периода",
    )
    confidence_level = models.PositiveIntegerField(
        default=50,
        verbose_name="Уверенность (%)",
        help_text="Уровень уверенности в прогнозе (0-100)",
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Примечания",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Прогноз"
        verbose_name_plural = "Прогнозы"
        ordering = ["-period_year", "-period_month", "-forecast_type"]
        unique_together = [["company", "forecast_type", "period_month", "period_year"]]

    def __str__(self):
        return f"{self.forecast_type} — {self.period_month}/{self.period_year} ({self.estimated_amount})"

    @property
    def variance(self):
        """Разница между прогнозом и фактом."""
        if self.actual_amount is None:
            return None
        return self.actual_amount - self.estimated_amount

    @property
    def variance_percent(self):
        """Разница в процентах."""
        if self.actual_amount is None or self.estimated_amount == 0:
            return None
        return round(
            ((self.actual_amount - self.estimated_amount) / self.estimated_amount) * 100,
            2,
        )

class PeriodComparison(models.Model):
    """
    Сравнение финансовых показателей между периодами.
    """
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="period_comparisons",
        verbose_name="Компания",
    )
    period_1_label = models.CharField(
        max_length=50,
        verbose_name="Период 1 (базовый)",
        help_text="Например: 'Январь 2026' или 'Q1 2026'",
    )
    period_2_label = models.CharField(
        max_length=50,
        verbose_name="Период 2 (сравнение)",
        help_text="Например: 'Февраль 2026' или 'Q1 2025'",
    )
    period_1_start = models.DateField(
        verbose_name="Начало периода 1",
    )
    period_1_end = models.DateField(
        verbose_name="Конец периода 1",
    )
    period_2_start = models.DateField(
        verbose_name="Начало периода 2",
    )
    period_2_end = models.DateField(
        verbose_name="Конец периода 2",
    )
    comparison_date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата сравнения",
    )

    class Meta:
        verbose_name = "Сравнение периодов"
        verbose_name_plural = "Сравнения периодов"
        ordering = ["-comparison_date"]

    def __str__(self):
        return f"{self.period_1_label} vs {self.period_2_label}"

    # Методы для получения данных будут в views
