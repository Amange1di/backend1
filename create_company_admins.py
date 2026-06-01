import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Company

# Получаем все компании
companies = Company.objects.all()
admin_user = User.objects.get(id=6)  # Ваш admin аккаунт (id=6)

print(f'Найдено компаний: {companies.count()}')

created_count = 0
for company in companies:
    # Проверяем, есть ли уже course_admin для этой компании
    existing_admins = User.objects.filter(
        role=User.Role.COURSE_ADMIN,
        company_name=company.name
    )
    
    if existing_admins.exists():
        print(f'  {company.name}: уже есть admin - {existing_admins.first().username}')
        continue
    
    # Создаём username на основе названия компании
    username = f"admin_{company.id}"
    password = f"Admin@{company.id}2024"  # Временный пароль
    
    # Проверяем, не занят ли username
    if User.objects.filter(username=username).exists():
        username = f"admin_{company.id}_{company.name[:3].lower().replace(' ', '')}"
    
    # Создаём course_admin
    admin = User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@edu.kg",
        first_name=company.name,
        role=User.Role.COURSE_ADMIN,
        company_name=company.name,
        phone=f"+996700{100000 + company.id}",
        address="Bishkek",
        max_managers=3,
        max_pages=1,
        max_blocks=7,
        created_by=admin_user,
    )
    
    created_count += 1
    print(f'  {company.name}: создан admin - {username} (пароль: {password})')

print(f'\nСоздано новых course_admin: {created_count}')
print(f'Всего course_admin теперь: {User.objects.filter(role=User.Role.COURSE_ADMIN).count()}')