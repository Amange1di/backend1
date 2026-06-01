import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import User, Company

# Находим компанию
company = Company.objects.get(name="Edu Center Pro")
print(f"Компания: {company.name} (ID: {company.id})")

# Находим всех преподавателей компании
teachers = User.objects.filter(role=User.Role.TEACHER, company=company)
print(f"Найдено преподавателей: {teachers.count()}")

# Обновляем пароль для всех
new_password = "password123"
count = 0
for teacher in teachers:
    teacher.set_password(new_password)
    teacher.save()
    print(f"  ✅ {teacher.first_name} {teacher.last_name} (@{teacher.username}) - пароль обновлён")
    count += 1

print(f"\n✅ Обновлено паролей: {count}")
print(f"🔐 Новый пароль для всех: {new_password}")
