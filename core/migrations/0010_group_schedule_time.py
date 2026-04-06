from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_group_schedule_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="schedule_time",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
