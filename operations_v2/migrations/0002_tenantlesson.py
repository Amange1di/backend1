from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('operations_v2', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='TenantLesson',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('starts_at', models.DateTimeField(db_index=True)),
                ('ends_at', models.DateTimeField()),
                ('room_name', models.CharField(max_length=120, blank=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='operations_v2.tenantgroup')),
            ],
            options={
                'ordering': ['starts_at', 'id'],
                'constraints': [models.CheckConstraint(condition=models.Q(ends_at__gt=models.F('starts_at')), name='v2_lesson_ends_after_start')],
            },
        ),
    ]
