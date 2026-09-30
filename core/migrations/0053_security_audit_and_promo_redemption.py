import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0052_contracttemplate"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromoRedemption",
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
                (
                    "activated_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promo_redemptions",
                        to="core.company",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redemptions",
                        to="core.promocode",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="promo_redemptions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-activated_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="promoredemption",
            constraint=models.UniqueConstraint(
                fields=("promo_code", "company"),
                name="uniq_promo_redemption_company",
            ),
        ),
        migrations.CreateModel(
            name="AuditLog",
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
                ("action", models.CharField(max_length=120)),
                (
                    "object_type",
                    models.CharField(blank=True, max_length=120),
                ),
                (
                    "object_id",
                    models.CharField(blank=True, max_length=120),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("before", models.JSONField(blank=True, default=dict)),
                ("after", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="core.company",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["company", "-created_at"],
                        name="core_audit_company_created_idx",
                    ),
                    models.Index(
                        fields=["actor", "-created_at"],
                        name="core_audit_actor_created_idx",
                    ),
                    models.Index(
                        fields=["action", "-created_at"],
                        name="core_audit_action_created_idx",
                    ),
                ],
            },
        ),
    ]
