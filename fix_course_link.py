import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import User, Course, Company

# Находим преподавателя
teacher = User.objects.get(username="togru.abdyldayev")
print(f"Преподаватель: {teacher.first_name} {teacher.last_name} (@{teacher.username})")
print(f"Роль: {teacher.role}")
print(f"Компания: {teacher.company.name if teacher.company else 'НЕТ'}")

# Находим курс B2-C1
course = Course.objects.get(title="Продвинутый английский (B2-C1)")
print(f"\nКурс: {course.title} (ID: {course.id})")

# Проверяем текущих админов курса
print(f"\nТекущие админы курса ({course.admins.count()}):")
for admin in course.admins.all():
    print(f"  • {admin.first_name} {admin.last_name} (@{admin.username}) - {admin.role}")

# Проверяем, есть ли уже связь
if teacher in course.admins.all():
    print(f"\n✅ Преподаватель УЖЕ связан с курсом!")
else:
    print(f"\n❌ Преподаватель НЕ связан с курсом. Добавляю...")
    course.admins.add(teacher)
    print(f"✅ Добавлено!")

# Проверка после добавления
print(f"\nПроверка после добавления:")
print(f"Админов курса: {course.admins.count()}")
for admin in course.admins.all():
    print(f"  • {admin.first_name} {admin.last_name} (@{admin.username})")

# Также проверяем с другой стороны
print(f"\nКурсы преподавателя ({teacher.admin_courses.count()}):")
for c in teacher.admin_courses.all():
    print(f"  • {c.title}")
