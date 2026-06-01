import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import User, Course

# Находим преподавателя и курс
teacher = User.objects.get(username="togru.abdyldayev")
course = Course.objects.get(title="Продвинутый английский (B2-C1)")

print(f"Преподаватель: {teacher.username} (ID: {teacher.id}, роль: {teacher.role})")
print(f"Курс: {course.title} (ID: {course.id})")

# Проверяем текущую связь
admins = list(course.admins.all())
print(f"\nТекущие админы курса ({len(admins)}):")
for a in admins:
    print(f"  - {a.username} (ID: {a.id}, роль: {a.role})")

# Проверяем, есть ли учитель в списке
if teacher in admins:
    print(f"\n✅ Преподаватель УЖЕ в списке админов!")
else:
    print(f"\n❌ Преподавателя НЕТ в списке. Добавляем...")
    course.admins.add(teacher)
    course.save()
    print(f"✅ Добавлено!")

# Финальная проверка
print(f"\n--- ФИНАЛЬНАЯ ПРОВЕРКА ---")
final_admins = list(course.admins.all())
print(f"Админов курса: {len(final_admins)}")
for a in final_admins:
    print(f"  - {a.username} (ID: {a.id}, роль: {a.role})")

# Проверяем с другой стороны
teacher_courses = list(teacher.admin_courses.all())
print(f"\nКурсов у преподавателя: {len(teacher_courses)}")
for c in teacher_courses:
    print(f"  - {c.title} (ID: {c.id})")
