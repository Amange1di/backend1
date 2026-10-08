from django.db import migrations, models
import django.db.models.deletion


def create_main_branches(apps, schema_editor):
    Company = apps.get_model("core", "Company")
    Branch = apps.get_model("core", "Branch")
    User = apps.get_model("core", "User")
    Auditorium = apps.get_model("core", "Auditorium")
    Group = apps.get_model("core", "Group")
    TrialLead = apps.get_model("core", "TrialLead")
    Payment = apps.get_model("core", "Payment")
    Expense = apps.get_model("core", "Expense")
    for company in Company.objects.all().iterator():
        branch, _ = Branch.objects.get_or_create(company=company, is_main=True, defaults={"name": "Основной филиал", "is_active": True})
        User.objects.filter(company=company).update()
        for user in User.objects.filter(company=company):
            user.branches.add(branch)
        Auditorium.objects.filter(company=company, branch__isnull=True).update(branch=branch)
        Group.objects.filter(company=company, branch__isnull=True).update(branch=branch)
        TrialLead.objects.filter(company=company, branch__isnull=True).update(branch=branch)
        Payment.objects.filter(company=company, branch__isnull=True).update(branch=branch)
        Expense.objects.filter(company=company, branch__isnull=True).update(branch=branch)


class Migration(migrations.Migration):
    dependencies = [("core", "0057_student_user_multi_company")]
    operations = [
        migrations.AddField(model_name="company", name="branch_limit", field=models.PositiveIntegerField(default=1, verbose_name="Branch limit")),
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("address", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("is_main", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="branches", to="core.company")),
            ],
            options={"ordering": ("-is_main", "name")},
        ),
        migrations.AddConstraint(model_name="branch", constraint=models.UniqueConstraint(fields=("company", "name"), name="uniq_branch_name_per_company")),
        migrations.AddField(model_name="user", name="branches", field=models.ManyToManyField(blank=True, related_name="users", to="core.branch")),
        migrations.AddField(model_name="auditorium", name="branch", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="auditoriums", to="core.branch")),
        migrations.AddField(model_name="group", name="branch", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="groups", to="core.branch")),
        migrations.AddField(model_name="triallead", name="branch", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="trial_leads", to="core.branch")),
        migrations.AddField(model_name="payment", name="branch", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="core.branch")),
        migrations.AddField(model_name="expense", name="branch", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="expenses", to="core.branch")),
        migrations.RunPython(create_main_branches, migrations.RunPython.noop),
    ]
