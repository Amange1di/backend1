from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0060_restore_marketplace_category_domains"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="working_days",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
