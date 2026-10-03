from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import core.models.library


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0062_homeworktask_material_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="LibraryFolder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="library_folders", to="core.company")),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="library_folders", to="core.course")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="library_folders_created", to=settings.AUTH_USER_MODEL)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="children", to="core.libraryfolder")),
            ],
            options={"ordering": ("name",), "unique_together": {("company", "parent", "name")}},
        ),
        migrations.CreateModel(
            name="LibraryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("type", models.CharField(choices=[("homework","Homework"),("document","Document"),("pdf","PDF"),("video","Video"),("link","Link"),("image","Image"),("test","Test")], max_length=30)),
                ("file", models.FileField(blank=True, null=True, upload_to=core.models.library.build_library_upload_path)),
                ("url", models.URLField(blank=True, default="", max_length=1000)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("visibility", models.CharField(choices=[("private","Only me"),("company","Company")], default="company", max_length=20)),
                ("status", models.CharField(choices=[("draft","Draft"),("active","Active"),("archived","Archived")], default="active", max_length=20)),
                ("usage_count", models.PositiveIntegerField(default=0)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="library_items", to="core.company")),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="library_items", to="core.course")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="library_items_created", to=settings.AUTH_USER_MODEL)),
                ("folder", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="items", to="core.libraryfolder")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="LibraryHomeworkTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("instruction", models.TextField(blank=True)),
                ("max_score", models.PositiveIntegerField(default=100)),
                ("default_deadline_days", models.PositiveIntegerField(default=2)),
                ("library_item", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="homework_template", to="core.libraryitem")),
            ],
        ),
        migrations.CreateModel(
            name="LibraryFavorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to="core.libraryitem")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="library_favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("item", "user")}},
        ),
        migrations.AddField(
            model_name="homeworktask",
            name="library_item",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_homework", to="core.libraryitem"),
        ),
        migrations.AddIndex(model_name="libraryitem", index=models.Index(fields=["company","status"], name="core_librar_company_7756aa_idx")),
        migrations.AddIndex(model_name="libraryitem", index=models.Index(fields=["company","type"], name="core_librar_company_3d9b0e_idx")),
        migrations.AddIndex(model_name="libraryitem", index=models.Index(fields=["company","created_by"], name="core_librar_company_c12d4a_idx")),
    ]
