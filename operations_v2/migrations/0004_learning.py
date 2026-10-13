from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("operations_v2", "0003_tenantfinanceentry")]
    operations = [
        migrations.CreateModel(
            name="TenantLibraryItem",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("resource_url", models.URLField(max_length=1000, blank=True)),
                ("created_by_user_id", models.BigIntegerField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="library_items", to="operations_v2.tenantbranch")),
            ],
        ),
        migrations.CreateModel(
            name="TenantHomework",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("due_at", models.DateTimeField(null=True, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework", to="operations_v2.tenantgroup")),
                ("library_item", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="homework_assignments", to="operations_v2.tenantlibraryitem")),
            ],
        ),
    ]
