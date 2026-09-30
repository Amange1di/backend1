from django.db import models
from django.utils.translation import gettext_lazy as _


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
