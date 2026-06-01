import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import User, Course

# Получаем всех преподавателей Edu Center Pro
teachers = User.objects.filter(role=User.Role.TEACHER, company_name='Edu Center Pro')
print(f'Всего преподавателей: {teachers.count()}')
print()
for teacher in teachers:
    courses = teacher.teaching_courses.all()
    print(f'{teacher.first_name} {teacher.last_name} (@{teacher.username})')
    print(f'  teaching_courses: {list(courses.values_list("title", flat=True))}')
    print()
