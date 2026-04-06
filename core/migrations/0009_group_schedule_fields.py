from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_remove_group_telegram_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="schedule_days",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="group",
            name="lesson_duration_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="group",
            name="lessons_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
