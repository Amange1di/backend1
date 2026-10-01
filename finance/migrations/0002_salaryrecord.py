from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0056_company_billing"),
    ]

    operations = [
        migrations.CreateModel(
            name="SalaryRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField()),
                ("month", models.PositiveIntegerField()),
                ("base_salary", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("percent_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("bonus_amount", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("status", models.CharField(choices=[("pending", "Ожидает"), ("paid", "Оплачено")], default="pending", max_length=20)),
                ("paid_at", models.DateField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="salary_records", to="core.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="salary_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-year", "-month", "employee__first_name")},
        ),
        migrations.AddConstraint(
            model_name="salaryrecord",
            constraint=models.UniqueConstraint(
                fields=("company", "employee", "year", "month"),
                name="uniq_salary_record_company_employee_month",
            ),
        ),
    ]
