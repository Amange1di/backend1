from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0072_landing_content_agreement"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentDispatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("content_snapshot", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="document_dispatches", to="core.company")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_documents", to=settings.AUTH_USER_MODEL)),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dispatches", to="core.contracttemplate")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="DocumentReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                ("viewed_at", models.DateTimeField(blank=True, null=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("dispatch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to="core.documentdispatch")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="document_receipts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-sent_at",)},
        ),
        migrations.AddConstraint(model_name="documentreceipt", constraint=models.UniqueConstraint(fields=("dispatch", "recipient"), name="unique_dispatch_recipient")),
    ]
