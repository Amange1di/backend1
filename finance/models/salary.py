from django.conf import settings
from django.db import models


class SalaryRecord(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
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

    def __str__(self):
        return (
            f"{self.employee} — {self.month:02d}.{self.year}: "
            f"{self.total_amount}"
        )
