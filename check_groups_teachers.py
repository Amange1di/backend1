import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Course, Group

print("Проверка групп и преподавателей...")
print()

# Проверка групп для Edu Center Pro
groups = Group.objects.filter(company_name='Edu Center Pro')
print(f"Групп для Edu Center Pro: {groups.count()}")
print()

for group in groups:
    teacher = group.teacher
    course = group.course
    print(f"Группа: {group.name}")
    print(f"  Курс: {course.title if course else 'НЕТ'}")
    print(f"  Преподаватель: {teacher.first_name} {teacher.last_name} (@{teacher.username})" if teacher else "  Преподаватель: НЕТ")
    if teacher:
        teacher_courses = list(teacher.teaching_courses.all().values_list('title', flat=True))
        print(f"  teaching_courses у преподавателя: {teacher_courses if teacher_courses else 'ПУСТО'}")
    print()
