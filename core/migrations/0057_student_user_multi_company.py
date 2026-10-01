from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0056_company_billing"),
    ]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="student_profiles",
                to="core.user",
            ),
        ),
    ]
