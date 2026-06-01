import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, Course, Group, Student

# Получаем компанию
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания не найдена!")
    exit(1)

print("="*60)
print(f"Исправление привязок для: {company.name}")
print("="*60)

# 1. Обновляем пользователей (учителя, менеджеры, админы)
print("\n👥 Обновление пользователей...")
users_updated = 0

# Учителя
teachers = User.objects.filter(role=User.Role.TEACHER).exclude(company=company)
for user in teachers:
    if user.first_name in ['Айжан', 'Бакыт', 'Каныбек', 'Дилшод', 'Эльмира', 'Нурзат', 'Талант', 'Айсулуу', 'Жаныбек', 'Гульнара']:
        user.company = company
        user.company_name = company.name
        user.save()
        users_updated += 1
        print(f"  ✅ Учитель: {user.first_name} {user.last_name}")

# Менеджеры
managers = User.objects.filter(role=User.Role.MANAGER).exclude(company=company)
for user in managers:
    if 'smartkids' in user.username.lower():
        user.company = company
        user.company_name = company.name
        user.save()
        users_updated += 1
        print(f"  ✅ Менеджер: {user.username}")

# Админы
admins = User.objects.filter(role=User.Role.COURSE_ADMIN).exclude(company=company)
for user in admins:
    if 'smartkids' in user.username.lower():
        user.company = company
        user.company_name = company.name
        user.save()
        users_updated += 1
        print(f"  ✅ Админ: {user.username}")

# Студенты (User)
students_users = User.objects.filter(role=User.Role.STUDENT).exclude(company=company)
for user in students_users:
    if user.first_name in ['Али', 'Айша', 'Бакыт', 'Дияра', 'Эмир', 'Айым', 'Талант', 'Саида', 'Каныбек', 'Нургуль', 
                           'Максим', 'Фарход', 'Сергей', 'Татьяна', 'Хуршед', 'Вадим', 'Роза', 'Эдиге', 'Бахтиёр']:
        user.company = company
        user.company_name = company.name
        user.save()
        users_updated += 1

print(f"\n✅ Обновлено пользователей: {users_updated}")

# 2. Обновляем профили студентов
print("\n📚 Обновление профилей студентов...")
student_profiles = Student.objects.filter(company=company)
for student in student_profiles:
    student.company_name = company.name
    student.save()

print(f"✅ Профилей обновлено: {student_profiles.count()}")

# 3. Проверяем курсы
print("\n📖 Проверка курсов...")
courses = Course.objects.filter(admins__company=company).distinct()
for course in courses:
    print(f"  ✅ Курс: {course.title}")

print(f"\n✅ Курсов: {courses.count()}")

# 4. Проверяем группы
print("\n📋 Проверка групп...")
groups = Group.objects.filter(company=company)
for group in groups:
    print(f"  ✅ Группа: {group.name}")

print(f"\n✅ Групп: {groups.count()}")

# 5. Итоговая статистика
print("\n" + "="*60)
print("ИТОГОВАЯ СТАТИСТИКА:")
print("="*60)
print(f"Компания: {company.name}")
print(f"Учителя (User): {User.objects.filter(role=User.Role.TEACHER, company=company).count()}")
print(f"Менеджеры (User): {User.objects.filter(role=User.Role.MANAGER, company=company).count()}")
print(f"Админы (User): {User.objects.filter(role=User.Role.COURSE_ADMIN, company=company).count()}")
print(f"Студенты (User): {User.objects.filter(role=User.Role.STUDENT, company=company).count()}")
print(f"Профили студентов: {Student.objects.filter(company=company).count()}")
print(f"Курсы: {courses.count()}")
print(f"Группы: {groups.count()}")

print("\n✅ Все привязки исправлены!")
print("\nЛогин: manager_smartkids_1 / admin123")
