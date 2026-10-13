from django.db import models

from .models import TenantBranch


class TenantFinanceEntry(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    branch = models.ForeignKey(TenantBranch, on_delete=models.PROTECT, related_name="finance_entries")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    occurred_on = models.DateField(db_index=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="v2_finance_amount_positive",
            ),
        ]
