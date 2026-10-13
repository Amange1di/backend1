from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='TenantBranch',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('company_id', models.BigIntegerField(db_index=True)),
                ('name', models.CharField(max_length=200)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('company_id', 'name'), name='v2_unique_tenant_branch')]},
        ),
        migrations.CreateModel(
            name='TenantStudent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('central_user_id', models.BigIntegerField(blank=True, db_index=True, null=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(blank=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='students', to='operations_v2.tenantbranch')),
            ],
        ),
        migrations.CreateModel(
            name='TenantGroup',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('teacher_user_id', models.BigIntegerField(blank=True, null=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='groups', to='operations_v2.tenantbranch')),
                ('students', models.ManyToManyField(blank=True, related_name='groups', to='operations_v2.tenantstudent')),
            ],
        ),
        migrations.CreateModel(
            name='TenantAttendance',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('present', models.BooleanField(default=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='operations_v2.tenantgroup')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='operations_v2.tenantstudent')),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('group', 'student', 'date'), name='v2_unique_attendance')]},
        ),
    ]
