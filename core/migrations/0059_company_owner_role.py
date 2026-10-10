from django.db import migrations, models


def promote_company_owners(apps, schema_editor):
    Company = apps.get_model("core", "Company")
    User = apps.get_model("core", "User")
    owner_ids = Company.objects.exclude(owner_id=None).values_list("owner_id", flat=True)
    User.objects.filter(id__in=owner_ids, role="course_admin").update(role="company_owner")


def rollback_company_owners(apps, schema_editor):
    User = apps.get_model("core", "User")
    User.objects.filter(role="company_owner").update(role="course_admin")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0058_multi_branch"),
        ("core", "0058_payment_received_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("super_admin", "Super Admin"),
                    ("admin", "Admin"),
                    ("company_owner", "Company owner"),
                    ("course_admin", "Branch admin"),
                    ("manager", "Manager"),
                    ("teacher", "Teacher"),
                    ("student", "Student"),
                ],
                default="teacher",
                max_length=20,
            ),
        ),
        migrations.RunPython(promote_company_owners, rollback_company_owners),
    ]
