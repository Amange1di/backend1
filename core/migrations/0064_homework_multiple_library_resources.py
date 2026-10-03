from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0063_library"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeworktask",
            name="library_items",
            field=models.ManyToManyField(
                blank=True,
                related_name="homework_tasks",
                to="core.libraryitem",
            ),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="library_resource_snapshots",
            field=models.JSONField(
                blank=True,
                default=list,
            ),
        ),
    ]
