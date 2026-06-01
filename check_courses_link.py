import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import User, Course, Company

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
print(f"Компания: {company.name} (ID: {company.id})")

# Находим Course Admin
admin = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).first()
if admin:
    print(f"Course Admin: {admin.username} (ID: {admin.id})")
    print(f"Связь Admin-Company: {admin.company.name if admin.company else 'НЕТ'}")
else:
    print("❌ Course Admin не найден!")

# Получаем все курсы
all_courses = Course.objects.all()
print(f"\n{'='*60}")
print(f"ВСЕ КУРСЫ В БАЗЕ: {all_courses.count()}")
print(f"{'='*60}")

for course in all_courses:
    print(f"\n📚 {course.title} (ID: {course.id})")
    print(f"   Цена: {course.price} сом, Длительность: {course.duration_weeks} недель")
    
    # Проверка админов курса
    course_admins = course.admins.all()
    print(f"   Админов курса: {course_admins.count()}")
    
    for ca in course_admins:
        role_str = "Course Admin" if ca.role == User.Role.COURSE_ADMIN else "Teacher" if ca.role == User.Role.TEACHER else ca.role
        company_str = f" (Компания: {ca.company.name if ca.company else 'НЕТ'})" if ca.company else " (Нет компании)"
        print(f"      • {ca.first_name} {ca.last_name} (@{ca.username}) - {role_str}{company_str}")

# Проверка преподавателей компании
print(f"\n{'='*60}")
print(f"ПРЕПОДАВАТЕЛИ КОМПАНИИ")
print(f"{'='*60}")
teachers = User.objects.filter(role=User.Role.TEACHER, company=company)
print(f"Найдено преподавателей: {teachers.count()}")

for teacher in teachers:
    # Какие курсы у этого преподавателя
    teacher_courses = teacher.admin_courses.all()
    courses_str = ", ".join([c.title for c in teacher_courses]) if teacher_courses else "НЕТ КУРСОВ"
    print(f"  • {teacher.first_name} {teacher.last_name} (@{teacher.username})")
    print(f"    Курсы: {courses_str}")
