import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company

print("=== Менеджеры компании 'Edu Center Pro' ===")
company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    managers = User.objects.filter(role=User.Role.MANAGER, company=company)
    print(f"Найдено менеджеров: {managers.count()}")
    for m in managers:
        print(f"  - {m.username} ({m.first_name} {m.last_name})")
        print(f"    Company: {m.company}")
        print(f"    Company name: {m.company_name}")
else:
    print("Компания не найдена!")

print("\n=== Все менеджеры в системе ===")
all_managers = User.objects.filter(role=User.Role.MANAGER)
print(f"Всего менеджеров: {all_managers.count()}")
for m in all_managers[:10]:
    print(f"  - {m.username}: company={m.company}, company_name={m.company_name}")
