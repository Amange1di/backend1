from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_user_teaching_courses"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="color",
            field=models.CharField(default="#45B2EF", max_length=7),
        ),
        migrations.AddField(
            model_name="user",
            name="salary_rate",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="working_hours",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
