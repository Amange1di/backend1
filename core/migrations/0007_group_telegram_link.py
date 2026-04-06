from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_student_company_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="telegram_link",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
