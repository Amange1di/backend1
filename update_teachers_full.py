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
if not admin:
    print("Ошибка: Course Admin не найден!")
    exit(1)

# Получаем все курсы компании
company_courses = list(admin.admin_courses.all())
print(f"Курсов в компании: {len(company_courses)}")

# Находим всех преподавателей компании
teachers = list(User.objects.filter(role=User.Role.TEACHER, company=company))
print(f"Преподавателей найдено: {len(teachers)}")

# Новые данные для преподавателей (логин + имя + фамилия)
teachers_data = [
    {"username": "ajbek.karaev", "first_name": "Айбек", "last_name": "Караев"},
    {"username": "gulnaz.alieva", "first_name": "Гульназ", "last_name": "Алиева"},
    {"username": "bekzat.usenov", "first_name": "Бекзат", "last_name": "Усенов"},
    {"username": "ajsuluu.mamytova", "first_name": "Айсулуу", "last_name": "Мамытова"},
    {"username": "dastan.ibraimov", "first_name": "Дастан", "last_name": "Ибраимов"},
    {"username": "nurjan.toktogulov", "first_name": "Нуржан", "last_name": "Токтогулов"},
    {"username": "kayyrgul.sadykova", "first_name": "Кайыргүл", "last_name": "Садыкова"},
    {"username": "azamat.jumabekov", "first_name": "Азамат", "last_name": "Жумабеков"},
    {"username": "roza.khozhabekova", "first_name": "Роза", "last_name": "Кожобекова"},
    {"username": "talant.asanov", "first_name": "Талант", "last_name": "Асанов"},
    {"username": "bakyt.iskaakova", "first_name": "Бакыт", "last_name": "Искакова"},
    {"username": "nurlan.matraimov", "first_name": "Нурлан", "last_name": "Матраимов"},
    {"username": "ajpinde.erkinova", "first_name": "Айпинде", "last_name": "Эркинова"},
    {"username": "zhanys.kudayberdiev", "first_name": "Жаныш", "last_name": "Кудайбердиев"},
    {"username": "togru.abdyldayev", "first_name": "Тогрул", "last_name": "Абдылдаев"},
]

print(f"\nОбновление логинов и ФИО...")
updated_count = 0
for teacher, data in zip(teachers, teachers_data):
    # Обновляем логин
    old_username = teacher.username
    teacher.username = data["username"]
    teacher.first_name = data["first_name"]
    teacher.last_name = data["last_name"]
    teacher.email = f"{data['username']}@edupro.kg"
    teacher.save()
    print(f"  ✅ {old_username} → {teacher.username} ({teacher.first_name} {teacher.last_name})")
    updated_count += 1

print(f"\n✅ Обновлено: {updated_count} преподавателей")

# Распределяем преподавателей по курсам (по 2 на каждый курс)
print(f"\nСвязывание преподавателей с курсами...")
for i, course in enumerate(company_courses):
    # Очищаем старых админов курсов (кроме Course Admin)
    current_admins = list(course.admins.all())
    for admin_user in current_admins:
        if admin_user.role == User.Role.TEACHER:
            course.admins.remove(admin_user)
    
    # Назначаем 2 преподавателей на курс
    teacher1 = teachers[i * 2] if i * 2 < len(teachers) else None
    teacher2 = teachers[i * 2 + 1] if i * 2 + 1 < len(teachers) else None
    
    if teacher1:
        course.admins.add(teacher1)
        print(f"  📚 {course.title}")
        print(f"      • {teacher1.first_name} {teacher.last_name}")
    if teacher2:
        course.admins.add(teacher2)
        print(f"      • {teacher2.first_name} {teacher2.last_name}")

print(f"\n✅ Преподаватели успешно связаны с курсами!")

# Проверка
print(f"\n{'='*50}")
print(f"ИТОГОВАЯ ИНФОРМАЦИЯ:")
print(f"{'='*50}")
for course in company_courses:
    course_teachers = [u for u in course.admins.all() if u.role == User.Role.TEACHER]
    print(f"\n📚 {course.title}")
    for teacher in course_teachers:
        print(f"   - {teacher.first_name} {teacher.last_name} (@{teacher.username})")
