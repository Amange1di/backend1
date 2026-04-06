from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_group_telegram_link"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="group",
            name="telegram_link",
        ),
    ]
