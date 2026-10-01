from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0055_archive_critical_records"),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanySubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan", models.CharField(choices=[("start", "Start"), ("growth", "Growth"), ("pro", "Pro")], default="start", max_length=20)),
                ("monthly_fee", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("active", "Активна"), ("overdue", "Просрочена"), ("paused", "Приостановлена")], default="active", max_length=20)),
                ("started_at", models.DateField(default=django.utils.timezone.localdate)),
                ("next_payment_date", models.DateField(blank=True, null=True)),
                ("auto_renew", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to="core.company")),
            ],
            options={"ordering": ("company__name",)},
        ),
        migrations.CreateModel(
            name="CompanyPlatformPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("due_date", models.DateField()),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("paid", "Оплачено"), ("pending", "Ожидает"), ("overdue", "Просрочено")], default="pending", max_length=20)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="platform_payments", to="core.company")),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="core.companysubscription")),
            ],
            options={
                "ordering": ("-period_start", "-created_at"),
                "constraints": [
                    models.UniqueConstraint(fields=("company", "period_start"), name="uniq_company_platform_payment_period"),
                ],
            },
        ),
    ]
