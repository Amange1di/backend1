from django.db import models
from django.utils import timezone


class CompanySubscription(models.Model):
    class Plan(models.TextChoices):
        START = "start", "Start"
        GROWTH = "growth", "Growth"
        PRO = "pro", "Pro"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        OVERDUE = "overdue", "Просрочена"
        PAUSED = "paused", "Приостановлена"

    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.START)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateField(default=timezone.localdate)
    next_payment_date = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("company__name",)

    def __str__(self) -> str:
        return f"{self.company.name} — {self.plan}"


class CompanyPlatformPayment(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", "Оплачено"
        PENDING = "pending", "Ожидает"
        OVERDUE = "overdue", "Просрочено"

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="platform_payments",
    )
    subscription = models.ForeignKey(
        "CompanySubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-period_start", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("company", "period_start"),
                name="uniq_company_platform_payment_period",
            )
        ]

    def __str__(self) -> str:
        return f"{self.company.name}: {self.amount} ({self.period_start:%m.%Y})"
