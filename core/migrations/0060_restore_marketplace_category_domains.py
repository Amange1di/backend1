from django.db import migrations, models


CATEGORY_MAP = {
    "basic": "it",
    "content": "languages",
    "media": "music",
    "forms": "other",
    "data": "business",
    "interactive": "sports",
}


def remap_marketplace_categories(apps, schema_editor):
    Company = apps.get_model("core", "Company")
    JobVacancy = apps.get_model("core", "JobVacancy")
    PublicCourse = apps.get_model("core", "PublicCourse")

    for old_value, new_value in CATEGORY_MAP.items():
        Company.objects.filter(category=old_value).update(category=new_value)
        JobVacancy.objects.filter(category=old_value).update(category=new_value)
        PublicCourse.objects.filter(category=old_value).update(category=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0059_marketplace_category_taxonomy"),
    ]

    operations = [
        migrations.RunPython(
            remap_marketplace_categories,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="company",
            name="category",
            field=models.CharField(
                choices=[
                    ("it", "IT"),
                    ("languages", "Языки"),
                    ("crafts", "Ручная работа"),
                    ("sports", "Спорт"),
                    ("music", "Музыка"),
                    ("business", "Бизнес"),
                    ("other", "Другое"),
                ],
                max_length=20,
                verbose_name="Category",
            ),
        ),
        migrations.AlterField(
            model_name="jobvacancy",
            name="category",
            field=models.CharField(
                choices=[
                    ("it", "IT"),
                    ("languages", "Языки"),
                    ("crafts", "Ручная работа"),
                    ("sports", "Спорт"),
                    ("music", "Музыка"),
                    ("business", "Бизнес"),
                    ("other", "Другое"),
                ],
                max_length=20,
                verbose_name="Category",
            ),
        ),
        migrations.AlterField(
            model_name="publiccourse",
            name="category",
            field=models.CharField(
                choices=[
                    ("it", "IT"),
                    ("languages", "Языки"),
                    ("crafts", "Ручная работа"),
                    ("sports", "Спорт"),
                    ("music", "Музыка"),
                    ("business", "Бизнес"),
                    ("other", "Другое"),
                ],
                max_length=20,
                verbose_name="Category",
            ),
        ),
    ]
}
