from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_user_address_user_phone"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="max_managers",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Maximum number of managers this course admin can create",
            ),
        ),
    ]
