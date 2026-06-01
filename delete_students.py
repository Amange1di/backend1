import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")

# Удаляем всех студентов компании
students = User.objects.filter(role=User.Role.STUDENT, company=company)
count = students.count()
students.delete()
print(f'Удалено студентов: {count}')
