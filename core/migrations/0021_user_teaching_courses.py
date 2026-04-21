from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0020_task_is_seen"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="teaching_courses",
            field=models.ManyToManyField(
                blank=True, related_name="teachers", to="core.course"
            ),
        ),
    ]
