import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company

print("=== Пользователи для входа ===\n")

# Суперадмин
try:
    superadmin = User.objects.filter(role=User.Role.SUPER_ADMIN).first()
    if superadmin:
        print(f"Super Admin:")
        print(f"  Логин: {superadmin.username}")
        print(f"  Пароль: (установите через create_superuser.py)")
        print()
except:
    pass

# Менеджеры
print("Менеджеры 'Edu Center Pro':")
company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    managers = User.objects.filter(role=User.Role.MANAGER, company=company)
    for m in managers:
        print(f"  Логин: {m.username}")
        print(f"  Пароль: (установите через reset_password)")
        print()

# Курсовые админы
print("Курсовые админы:")
admins = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company)
for a in admins:
    print(f"  Логин: {a.username}")
    print(f"  Пароль: (установите через reset_password)")
    print()