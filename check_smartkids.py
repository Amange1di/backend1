import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, Course, Group, StudentCourse, TeacherCourse

# Получаем компанию
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания не найдена!")
    exit(1)

admin = User.objects.filter(username='admin_smartkids').first()
if not admin:
    print("❌ Админ не найден!")
    exit(1)

print("="*60)
print(f"Проверка данных для: {company.name}")
print("="*60)

# 1. Курсы
courses = Course.objects.filter(admins=admin)
print(f"\n📚 Курсы: {courses.count()}")
for course in courses:
    print(f"   - {course.title} (₽{course.price}, {course.duration_weeks} нед.)")

# 2. Учителя
teachers = User.objects.filter(company=company, role=User.Role.TEACHER)
print(f"\n👨‍🏫 Учителя: {teachers.count()}")
for teacher in teachers[:5]:
    print(f"   - {teacher.first_name} {teacher.last_name}")
if teachers.count() > 5:
    print(f"   ... и еще {teachers.count() - 5}")

# 3. Студенты
students = User.objects.filter(company=company, role=User.Role.STUDENT)
print(f"\n👨‍🎓 Студенты: {students.count()}")
for student in students[:5]:
    print(f"   - {student.first_name} {student.last_name}")
if students.count() > 5:
    print(f"   ... и еще {students.count() - 5}")

# 4. Группы
groups = Group.objects.filter(company=company)
print(f"\n📋 Группы: {groups.count()}")

# 5. Привязки студентов к курсам
student_courses = StudentCourse.objects.filter(course__admins=admin)
print(f"\n📝 Записи студентов к курсам: {student_courses.count()}")

# 6. Привязки учителей к курсам
teacher_courses = TeacherCourse.objects.filter(course__admins=admin)
print(f"\n📚 Привязки учителей к курсам: {teacher_courses.count()}")

print("\n" + "="*60)
print("Сводка:")
print("="*60)
print(f"Компания: {company.name}")
print(f"Курсы: {courses.count()}")
print(f"Учителя: {teachers.count()}")
print(f"Студенты: {students.count()}")
print(f"Группы: {groups.count()}")
print(f"Записи студентов: {student_courses.count()}")
print(f"Привязки учителей: {teacher_courses.count()}")

print("\n✅ Проверка завершена!")
