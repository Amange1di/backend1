import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Company, Course, User

# Проверяем компанию
company = Company.objects.get(name="Edu Center Pro")
print(f"Компания: {company.name} (ID: {company.id})")

# Проверка курсов (модель Course не имеет прямого поля company)
# Курсы связаны через admins (ManyToMany)
print(f"\n📚 Курсы в базе (всего): {Course.objects.count()}")
print("⚠️  Обратите внимание: Модель Course не имеет прямого поля 'company'")
print("   Курсы могут быть связаны только через поле 'admins' (Course Admin)")

# Проверка Course Admin
admins = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company)
print(f"\n👤 Course Admin'ы для этой компании: {admins.count()}")
for admin in admins:
    print(f"  - {admin.username} (ID: {admin.id})")
    # Проверка курсов этого админа
    admin_courses = admin.admin_courses.all()
    print(f"    Курсы админа: {admin_courses.count()}")
    for course in admin_courses:
        print(f"      • {course.title}")

# Проверка, есть ли пользователи с company_name (устаревшее поле)
users_with_company_name = User.objects.filter(company_name=company.name)
print(f"\n👥 Пользователей с company_name='{company.name}': {users_with_company_name.count()}")