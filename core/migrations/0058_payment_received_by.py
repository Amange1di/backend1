from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0057_student_user_multi_company"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="received_by",
            field=models.ForeignKey(
                blank=True,
                help_text="Сотрудник, который принял/зарегистрировал оплату",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="received_payments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
}
