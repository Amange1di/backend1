from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_salary_payments(apps, schema_editor):
    SalaryRecord = apps.get_model("finance", "SalaryRecord")
    SalaryPayment = apps.get_model("finance", "SalaryPayment")

    for record in SalaryRecord.objects.filter(status="paid"):
        total = (
            (record.base_salary or Decimal("0"))
            + (record.percent_amount or Decimal("0"))
            + (record.bonus_amount or Decimal("0"))
        )
        if total <= 0:
            continue
        SalaryPayment.objects.create(
            salary_record=record,
            amount=total,
            paid_at=record.paid_at,
            payment_type="salary",
            note="Перенесено из предыдущей системы выплат",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0002_salaryrecord"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="salaryrecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Ожидает"),
                    ("partial", "Частично оплачено"),
                    ("paid", "Оплачено"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="SalaryPayment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("paid_at", models.DateField()),
                (
                    "payment_type",
                    models.CharField(
                        choices=[
                            ("advance", "Аванс"),
                            ("salary", "Зарплата"),
                            ("other", "Другое"),
                        ],
                        default="salary",
                        max_length=20,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_salary_payments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "salary_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="finance.salaryrecord",
                    ),
                ),
            ],
            options={"ordering": ("paid_at", "id")},
        ),
        migrations.RunPython(
            backfill_salary_payments,
            migrations.RunPython.noop,
        ),
    ]
}
