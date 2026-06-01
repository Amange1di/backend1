import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Course, Company

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
admin = User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).first()

if not admin:
    print("Course Admin не найден!")
    exit(1)

company_courses = list(admin.admin_courses.all())
teachers = list(User.objects.filter(role=User.Role.TEACHER, company=company))

print(f"Компания: {company.name}")
print(f"Курсов: {len(company_courses)}")
print(f"Преподавателей: {len(teachers)}")
print()

# Проверка связи через Course.admins
for course in company_courses:
    course_teachers = [u for u in course.admins.all() if u.role == User.Role.TEACHER]
    print(f"Курс: {course.title}")
    print(f"  Преподаватели через course.admins: {len(course_teachers)}")
    for t in course_teachers:
        print(f"    - {t.first_name} {t.last_name}")
    print()

# Проверка связи через User.teaching_courses
print("\n=== Проверка через User.teaching_courses ===")
for teacher in teachers[:3]:
    courses_via_field = list(teacher.teaching_courses.all().values_list('title', flat=True))
    print(f"{teacher.username}: {courses_via_field}")
