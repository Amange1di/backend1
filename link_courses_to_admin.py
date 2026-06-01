import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Company, Course, User

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
print(f"Компания: {company.name} (ID: {company.id})")

# Находим Course Admin для этой компании
admin = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).first()
if not admin:
    print("Ошибка: Course Admin не найден для этой компании!")
    exit(1)

print(f"\nCourse Admin: {admin.username} (ID: {admin.id})")

# Получаем все курсы
all_courses = Course.objects.all()
print(f"Всего курсов в базе: {all_courses.count()}")

# Назначаем все курсы этому админу
print(f"\nНазначение курсов админу...")
for course in all_courses:
    # Проверяем, уже ли назначен
    if admin in course.admins.all():
        print(f"  ⏭️  {course.title} - уже назначен")
    else:
        course.admins.add(admin)
        print(f"  ✅ {course.title} - назначен")

# Проверка
admin_courses = admin.admin_courses.all()
print(f"\n✅ Теперь у админа {admin.username} {admin_courses.count()} курс(ов):")
for course in admin_courses:
    print(f"  • {course.title} (ID: {course.id})")
