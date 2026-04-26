from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_student_access_security"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomeworkTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(blank=True, max_length=200)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("attachment", models.FileField(blank=True, null=True, upload_to=core.models.build_homework_upload_path)),
                ("deadline", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework_tasks", to="core.group")),
                ("teacher", models.ForeignKey(limit_choices_to={"role": "teacher"}, on_delete=django.db.models.deletion.CASCADE, related_name="homework_tasks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="HomeworkSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer_text", models.TextField(blank=True)),
                ("file", models.FileField(blank=True, null=True, upload_to=core.models.build_homework_upload_path)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("reviewed", "Reviewed"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("grade", models.PositiveIntegerField(blank=True, null=True)),
                ("teacher_comment", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework_submissions", to="core.student")),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="core.homeworktask")),
            ],
            options={
                "ordering": ("-submitted_at",),
                "unique_together": {("task", "student")},
            },
        ),
    ]
