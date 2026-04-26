from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_user_teacher_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="is_login_allowed",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="student",
            name="can_login",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="is_student_cabinet_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="must_set_password",
            field=models.BooleanField(default=False),
        ),
    ]
