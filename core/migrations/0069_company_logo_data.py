from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0068_alter_company_owner')]
    operations = [migrations.AddField(model_name='company', name='logo_data', field=models.TextField(blank=True, default=''))]
