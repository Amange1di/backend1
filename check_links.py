import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import Company, User

# Проверка связи
print("Проверка связи компаний с пользователями:\n")
for company in Company.objects.all()[:4]:
    owner = company.owner
    print(f'Компания: {company.name}')
    print(f'  Владелец: {owner.username}')
    print(f'  - company: {owner.company.name if owner.company else None}')
    print(f'  - company_name: {owner.company_name}')
    print(f'  - Студентов: {company.students.count()}')
    print(f'  - Групп: {company.groups.count()}')
    print()
