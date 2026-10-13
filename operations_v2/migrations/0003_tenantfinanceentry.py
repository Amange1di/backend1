from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("operations_v2", "0002_tenantlesson")]
    operations = [
        migrations.CreateModel(
            name="TenantFinanceEntry",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("kind", models.CharField(max_length=10, choices=[("income", "Income"), ("expense", "Expense")])),
                ("amount", models.DecimalField(max_digits=14, decimal_places=2)),
                ("occurred_on", models.DateField(db_index=True)),
                ("description", models.CharField(max_length=255, blank=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finance_entries", to="operations_v2.tenantbranch")),
            ],
            options={"constraints": [
                models.CheckConstraint(condition=models.Q(amount__gt=0), name="v2_finance_amount_positive"),
            ]},
        ),
    ]
