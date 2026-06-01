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

print(f"Course Admin: {admin.username}")

# Получаем все курсы компании (назначенные админу)
company_courses = list(admin.admin_courses.all())
print(f"Курсов в компании: {len(company_courses)}")

if not company_courses:
    print("Ошибка: Нет курсов для связи с преподавателями!")
    exit(1)

# Список преподавателей
teachers_data = [
    {"username": "teacher_sarah", "first_name": "Сара", "last_name": "Джонсон", "phone": "+996555100001", "email": "sarah@edupro.kg"},
    {"username": "teacher_dmitry", "first_name": "Дмитрий", "last_name": "Иванов", "phone": "+996555100002", "email": "dmitry@edupro.kg"},
    {"username": "teacher_ayana", "first_name": "Аяна", "last_name": "Алиева", "phone": "+996555100003", "email": "ayana@edupro.kg"},
    {"username": "teacher_john", "first_name": "Джон", "last_name": "Смит", "phone": "+996555100004", "email": "john@edupro.kg"},
    {"username": "teacher_maria", "first_name": "Мария", "last_name": "Петрова", "phone": "+996555100005", "email": "maria@edupro.kg"},
    {"username": "teacher_alex", "first_name": "Александр", "last_name": "Ким", "phone": "+996555100006", "email": "alex@edupro.kg"},
    {"username": "teacher_elena", "first_name": "Елена", "last_name": "Соколова", "phone": "+996555100007", "email": "elena@edupro.kg"},
    {"username": "teacher_david", "first_name": "Дэвид", "last_name": "Браун", "phone": "+996555100008", "email": "david@edupro.kg"},
    {"username": "teacher_nazira", "first_name": "Назира", "last_name": "Осмонова", "phone": "+996555100009", "email": "nazira@edupro.kg"},
    {"username": "teacher_michael", "first_name": "Майкл", "last_name": "Джонс", "phone": "+996555100010", "email": "michael@edupro.kg"},
    {"username": "teacher_olga", "first_name": "Ольга", "last_name": "Васильева", "phone": "+996555100011", "email": "olga@edupro.kg"},
    {"username": "teacher_ryan", "first_name": "Райан", "last_name": "Уилсон", "phone": "+996555100012", "email": "ryan@edupro.kg"},
    {"username": "teacher_gulnara", "first_name": "Гульнара", "last_name": "Каримова", "phone": "+996555100013", "email": "gulnara@edupro.kg"},
    {"username": "teacher_james", "first_name": "Джеймс", "last_name": "Тейлор", "phone": "+996555100014", "email": "james@edupro.kg"},
    {"username": "teacher_anna", "first_name": "Анна", "last_name": "Новикова", "phone": "+996555100015", "email": "anna@edupro.kg"},
]

print(f"\nСоздание {len(teachers_data)} преподавателей...")

created_count = 0
for teacher_data in teachers_data:
    # Проверяем, существует ли пользователь
    if User.objects.filter(username=teacher_data["username"]).exists():
        print(f"  ⏭️  {teacher_data['first_name']} {teacher_data['last_name']} - уже существует")
        continue
    
    # Создаём пользователя
    user = User.objects.create_user(
        username=teacher_data["username"],
        email=teacher_data["email"],
        first_name=teacher_data["first_name"],
        last_name=teacher_data["last_name"],
        phone=teacher_data["phone"],
        role=User.Role.TEACHER,
        company=company,
    )
    
    # Устанавливаем пароль по умолчанию
    user.set_password("teacher123")
    user.save()
    
    print(f"  ✅ {user.first_name} {user.last_name} (@{user.username}) - создан")
    created_count += 1

print(f"\n✅ Создано преподавателей: {created_count}")

# Распределяем преподавателей по курсам
print(f"\nРаспределение преподавателей по курсам...")
teachers = User.objects.filter(role=User.Role.TEACHER, company=company)
print(f"Всего преподавателей: {teachers.count()}")

for i, course in enumerate(company_courses):
    # Берём 2 преподавателей на каждый курс
    assigned_teachers = list(teachers)[i*2:(i*2)+2]
    for teacher in assigned_teachers:
        if teacher not in course.admins.all():
            course.admins.add(teacher)
        print(f"  📚 {course.title} - добавлен {teacher.first_name} {teacher.last_name}")

print(f"\n✅ Преподаватели успешно распределены по курсам!")
print(f"📊 Итого: {teachers.count()} преподавателей на {company_courses.count()} курсов")