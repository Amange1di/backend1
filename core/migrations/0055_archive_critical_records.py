from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0054_firstlogincredential"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="archived_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="group",
            name="archived_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="archived_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
    ]
