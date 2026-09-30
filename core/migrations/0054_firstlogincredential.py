import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0053_security_audit_and_promo_redemption"),
    ]

    operations = [
        migrations.CreateModel(
            name="FirstLoginCredential",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password_hash", models.CharField(max_length=128)),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="first_login_credential",
                        to="core.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "First Login Credential",
                "verbose_name_plural": "First Login Credentials",
            },
        ),
    ]
