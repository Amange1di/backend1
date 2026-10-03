from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0061_user_working_days"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeworktask",
            name="material_url",
            field=models.URLField(
                blank=True,
                default="",
                max_length=1000,
            ),
        ),
    ]
