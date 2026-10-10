from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0067_merge_multibranch_platformapplication"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="owner",
            field=models.ForeignKey(
                limit_choices_to={"role__in": ["company_owner", "course_admin"]},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="companies",
                to="core.user",
            ),
        ),
    ]
