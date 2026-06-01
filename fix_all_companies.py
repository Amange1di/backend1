import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company

# Получаем компанию
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания не найдена!")
    exit(1)

print(f"🔄 Обновление всех пользователей для: {company.name}")
print("="*60)

# Обновляем всех пользователей с company_name = 'Smart Kids Center'
users_updated = 0

for role in [User.Role.TEACHER, User.Role.MANAGER, User.Role.COURSE_ADMIN, User.Role.STUDENT]:
    users = User.objects.filter(role=role, company_name='Smart Kids Center').exclude(company=company)
    for user in users:
        user.company = company
        user.company_name = company.name
        user.save()
        users_updated += 1
        print(f"✅ {role}: {user.username} - {user.first_name} {user.last_name}")

print(f"\n✅ Обновлено пользователей: {users_updated}")
print(f"\n📊 Итого по компании:")
print(f"  Учителя: {User.objects.filter(role=User.Role.TEACHER, company=company).count()}")
print(f"  Менеджеры: {User.objects.filter(role=User.Role.MANAGER, company=company).count()}")
print(f"  Админы: {User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).count()}")
print(f"  Студенты: {User.objects.filter(role=User.Role.STUDENT, company=company).count()}")