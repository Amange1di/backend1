from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0071_landingsection_header_choice"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="LandingContentAgreement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("create", "Landing page creation"), ("submit", "Submission for moderation")], max_length=10)),
                ("agreement_version", models.CharField(default="1.0", max_length=20)),
                ("accepted_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="landing_agreements", to="core.company")),
                ("page", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="agreements", to="core.landingpage")),
                ("user", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="landing_agreements", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-accepted_at", "-id")},
        ),
        migrations.AddIndex(model_name="landingcontentagreement", index=models.Index(fields=["company", "-accepted_at"], name="landing_agreement_comp_idx")),
    ]
