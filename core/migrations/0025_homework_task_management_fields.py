from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_homework_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="homeworktask",
            name="allow_late",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="grace_period_minutes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="hard_deadline",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="is_extra_task",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="is_published",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="lesson_number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="publish_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="students",
            field=models.ManyToManyField(blank=True, related_name="individual_tasks", to="core.student"),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="target_type",
            field=models.CharField(choices=[("all_group", "All group"), ("specific_students", "Specific students")], default="all_group", max_length=32),
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="task_type",
            field=models.CharField(choices=[("homework", "Homework"), ("quiz", "Quiz"), ("project", "Project"), ("exam", "Exam")], default="homework", max_length=20),
        ),
        migrations.CreateModel(
            name="HomeworkTaskAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=core.models.build_homework_upload_path)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="core.homeworktask")),
            ],
        ),
    ]
