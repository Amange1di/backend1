from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('tenancy_v2', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='companymembership',
            name='branch_id',
            field=models.BigIntegerField(null=True, blank=True, db_index=True),
        ),
    ]
