from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class BudgetCategory(models.TextChoices):
    """Категории бюджетов."""
    SALARY = "salary", _("Зарплата")
    RENT = "rent", _("Аренда")
    UTILITIES = "utilities", _("Коммунальные услуги")
    MATERIALS = "materials", _("Учебные материалы")
    MARKETING = "marketing", _("Маркетинг")
    EQUIPMENT = "equipment", _("Оборудование")
    TAX = "tax", _("Налоги")
    OTHER = "other", _("Прочее")


class Budget(models.Model):
    """
    Бюджет компании на период.
    Устанавливает лимит расходов по категориям.
    """
    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="budgets",
        verbose_name="Компания",
    )
    category = models.CharField(
        max_length=20,
        choices=BudgetCategory.choices,
        verbose_name="Категория",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Лимит бюджета",
        help_text="Максимальная сумма расходов по этой категории",
    )
    period_start = models.DateField(
        verbose_name="Начало периода",
        help_text="Дата начала бюджетного периода",
    )
    period_end = models.DateField(
        verbose_name="Конец периода",
        help_text="Дата окончания бюджетного периода",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Если снят — бюджет не учитывается",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бюджет"
        verbose_name_plural = "Бюджеты"
        ordering = ["-period_end", "-created_at"]

    def __str__(self):
        return f"{self.category} — {self.period_start} / {self.period_end} ({self.amount})"

    @property
    def spent(self):
        """Сумма расходов по этой категории за период."""
        from core.models import Expense
        return (
            Expense.objects.filter(
                company=self.company,
                category=self.category,
                date__gte=self.period_start,
                date__lte=self.period_end,
            )
            .aggregate(total=models.Sum("amount"))["total"]
            or 0
        )

    @property
    def remaining(self):
        """Оставшаяся сумма бюджета."""
        return self.amount - self.spent

    @property
    def utilization_rate(self):
        """Процент использования бюджета (0-100)."""
        if self.amount == 0:
            return 0
        return round((self.spent / self.amount) * 100, 2)

    def check_over_budget(self):
        """Проверка превышения бюджета."""
        return self.spent > self.amount


class BudgetAlert(models.Model):
    """Уведомления о приближении к лимиту бюджета."""
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="Бюджет",
    )
    threshold = models.PositiveIntegerField(
        verbose_name="Порог (%)",
        help_text="Процент от бюджета, при котором сработает алерт",
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name="Отправлено",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Оповещение бюджета"
        verbose_name_plural = "Оповещения бюджетов"


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
            MinValueValidator(0),
            MaxValueValidator(100),
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
