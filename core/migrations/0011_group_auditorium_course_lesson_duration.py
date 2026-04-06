from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_group_schedule_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="lesson_duration_minutes",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="group",
            name="auditorium",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RemoveField(
            model_name="group",
            name="lesson_duration_minutes",
        ),
    ]
