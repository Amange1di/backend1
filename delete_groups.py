import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Group, Company

# Удаляем все группы Edu Center Pro
company = Company.objects.get(name='Edu Center Pro')
groups = Group.objects.filter(company=company)
count = groups.count()
groups.delete()
print(f'Удалено групп: {count}')
