from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum


class SalaryRecord(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        PARTIAL = "partial", "Частично оплачено"
        PAID = "paid", "Оплачено"

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="salary_records",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="salary_records",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    paid_at = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-year", "-month", "employee__first_name")
        constraints = [
            models.UniqueConstraint(
                fields=("company", "employee", "year", "month"),
                name="uniq_salary_record_company_employee_month",
            )
        ]

    @property
    def total_amount(self):
        return self.base_salary + self.percent_amount + self.bonus_amount

    @property
    def paid_amount(self):
        return (
            self.payments.aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

    @property
    def remaining_amount(self):
        return max(self.total_amount - self.paid_amount, Decimal("0"))

    def refresh_payment_status(self):
        paid = self.paid_amount
        total = self.total_amount

        if paid <= 0:
            status = self.Status.PENDING
            paid_at = None
        elif paid < total:
            status = self.Status.PARTIAL
            paid_at = None
        else:
            status = self.Status.PAID
            last_payment = self.payments.order_by("-paid_at", "-id").first()
            paid_at = last_payment.paid_at if last_payment else None

        changed = []
        if self.status != status:
            self.status = status
            changed.append("status")
        if self.paid_at != paid_at:
            self.paid_at = paid_at
            changed.append("paid_at")

        if changed:
            changed.append("updated_at")
            self.save(update_fields=changed)

    def __str__(self):
        return (
            f"{self.employee} — {self.month:02d}.{self.year}: "
            f"{self.total_amount}"
        )


class SalaryPayment(models.Model):
    class PaymentType(models.TextChoices):
        ADVANCE = "advance", "Аванс"
        SALARY = "salary", "Зарплата"
        OTHER = "other", "Другое"

    salary_record = models.ForeignKey(
        SalaryRecord,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateField()
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.SALARY,
    )
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_salary_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("paid_at", "id")

    def __str__(self):
        return (
            f"{self.salary_record} — {self.amount} "
            f"({self.get_payment_type_display()})"
        )
