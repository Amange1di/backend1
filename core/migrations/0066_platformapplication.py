from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0065_rename_libraryitem_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=200, verbose_name="Full Name")),
                ("center_name", models.CharField(max_length=200, verbose_name="Education Center")),
                ("phone", models.CharField(max_length=50, verbose_name="Phone Number")),
                ("comment", models.TextField(blank=True, verbose_name="Comment")),
                ("status", models.CharField(choices=[("new", "New"), ("processing", "In Processing"), ("approved", "Approved"), ("rejected", "Rejected")], default="new", max_length=20, verbose_name="Status")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Platform Application",
                "verbose_name_plural": "Platform Applications",
                "ordering": ("-created_at",),
            },
        ),
    ]
