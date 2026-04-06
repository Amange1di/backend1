from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_group_auditorium_course_lesson_duration"),
    ]

    operations = [
        migrations.CreateModel(
            name="Auditorium",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("number", models.CharField(blank=True, max_length=50)),
                ("company_name", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="group",
            name="auditorium",
        ),
        migrations.AddField(
            model_name="group",
            name="auditorium",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="groups", to="core.auditorium"),
        ),
    ]
