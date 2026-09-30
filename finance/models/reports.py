from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportType(models.TextChoices):
    """Типы бухгалтерских отчётов."""
    INCOME_STATEMENT = "income_statement", _("Отчёт о прибылях и убытках")
    BALANCE_SHEET = "balance_sheet", _("Баланс")
    CASH_FLOW = "cash_flow", _("Движение денежных средств")
    DEBT_REPORT = "debt_report", _("Отчёт по задолженностям")
    SALARY_REPORT = "salary_report", _("Отчёт по зарплатам")
    CUSTOM = "custom", _("Пользовательский")

class AccountingReport(models.Model):
    """
    Бухгалтерский отчёт.
    Генерируется на основе данных за период.
    """
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="accounting_reports",
        verbose_name="Компания",
    )
    report_type = models.CharField(
        max_length=30,
        choices=ReportType.choices,
        verbose_name="Тип отчёта",
    )
    period_start = models.DateField(
        verbose_name="Период с",
    )
    period_end = models.DateField(
        verbose_name="Период по",
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Сгенерирован",
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
        verbose_name="Сгенерирован пользователем",
    )
    pdf_file = models.FileField(
        upload_to="reports/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="PDF файл",
        help_text="Скачать PDF отчёт",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Примечания",
    )

    class Meta:
        verbose_name = "Бухгалтерский отчёт"
        verbose_name_plural = "Бухгалтерские отчёты"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.get_report_type_display()} — {self.period_start} / {self.period_end}"

class MonthlySummary(models.Model):
    """
    Ежемесячная сводка по компании.
    Автоматически заполняется в конце каждого месяца.
    """
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="monthly_summaries",
        verbose_name="Компания",
    )
    year = models.PositiveIntegerField(
        verbose_name="Год",
    )
    month = models.PositiveIntegerField(
        verbose_name="Месяц (1-12)",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ],
    )
    total_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Общий доход",
    )
    total_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Общие расходы",
    )
    total_salaries = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Зарплаты",
    )
    net_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Чистая прибыль",
    )
    total_students = models.PositiveIntegerField(
        default=0,
        verbose_name="Кол-во студентов",
    )
    total_groups = models.PositiveIntegerField(
        default=0,
        verbose_name="Кол-во групп",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ежемесячная сводка"
        verbose_name_plural = "Ежемесячные сводки"
        ordering = ["-year", "-month"]
        unique_together = [["company", "year", "month"]]

    def __str__(self):
        months = [
            "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
        ]
        month_name = months[self.month] if 1 <= self.month <= 12 else str(self.month)
        return f"{month_name} {self.year} — {self.company.name}"

    @property
    def profit_margin(self):
        """Рентабельность в процентах."""
        if self.total_income == 0:
            return 0
        return round((self.net_profit / self.total_income) * 100, 2)
