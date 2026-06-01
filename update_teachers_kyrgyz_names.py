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

# Кыргызские имена для преподавателей
kyrgyz_names = [
    {"first_name": "Айбек", "last_name": "Караев"},
    {"first_name": "Гульназ", "last_name": "Алиева"},
    {"first_name": "Бекзат", "last_name": "Усенов"},
    {"first_name": "Айсулуу", "last_name": "Мамытова"},
    {"first_name": "Дастан", "last_name": "Ибраимов"},
    {"first_name": "Нуржан", "last_name": "Токтогулов"},
    {"first_name": "Кайыргül", "last_name": "Садыкова"},
    {"first_name": "Азамат", "last_name": "Жумабеков"},
    {"first_name": "Роза", "last_name": "Кожобекова"},
    {"first_name": "Талант", "last_name": "Асанов"},
    {"first_name": "Бакыт", "last_name": "Искакова"},
    {"first_name": "Нурлан", "last_name": "Матраимов"},
    {"first_name": "Айпинде", "last_name": "Эркинова"},
    {"first_name": "Жаныш", "last_name": "Кудайбердиев"},
    {"first_name": "Тогрул", "last_name": "Абдылдаев"},
]

# Обновляем ФИО для всех
count = 0
for teacher, names in zip(teachers, kyrgyz_names):
    teacher.first_name = names["first_name"]
    teacher.last_name = names["last_name"]
    teacher.save()
    print(f"  ✅ {teacher.username} - {teacher.first_name} {teacher.last_name}")
    count += 1

print(f"\n✅ Обновлено ФИО: {count} преподавателей")
print(f"📝 Все имена теперь на кыргызском!")
