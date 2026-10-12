from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("core", "0069_company_logo_data")]

    operations = [
        migrations.RemoveField(
            model_name="studentapplication",
            name="budget",
        ),
    ]
