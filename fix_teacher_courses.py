import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Course, Group

print("Восстановление связей преподавателей с курсами...")
print()

# Получаем всех преподавателей
teachers = User.objects.filter(role=User.Role.TEACHER)
print(f"Всего преподавателей в базе: {teachers.count()}")
print()

updated_count = 0
for teacher in teachers:
    # Находим группы, где этот преподаватель
    groups = Group.objects.filter(teacher=teacher)
    courses = set()
    
    for group in groups:
        if group.course:
            courses.add(group.course)
    
    # Если есть курсы, но преподаватель не связан с ними
    existing_courses = set(teacher.teaching_courses.all())
    if courses and courses != existing_courses:
        teacher.teaching_courses.set(courses)
        teacher.save()
        updated_count += 1
        print(f"✓ {teacher.first_name} {teacher.last_name} (@{teacher.username})")
        print(f"  Назначено курсов: {list(courses.values_list('title', flat=True))}")
        print()

print(f"Обновлено преподавателей: {updated_count}")
print("Готово!")
