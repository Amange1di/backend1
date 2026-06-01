import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, Company, Course, LandingPage, LandingSection, TrialLead

# Создаем компанию
company, created = Company.objects.get_or_create(
    slug='smart-kids-center',
    defaults={
        'name': 'Smart Kids Center',
        'description': 'Центр развития детей. Английский язык, программирование, логика.',
        'category': 'education',
        'city': 'bishkek',
        'district': 'микрорайон Аламедин',
        'phone': '+996 555 123 456',
        'telegram': '@smartkidscenter',
        'whatsapp': '+996555123456',
        'website': 'https://smartkids.kg',
        'is_active': True,
    }
)

if created:
    print(f"✅ Компания создана: {company.name}")
else:
    print(f"ℹ️ Компания уже существует: {company.name}")
    # Обновляем компанию если нужно
    company.name = 'Smart Kids Center'
    company.save()

# Создаем курсового админа
admin, created = User.objects.get_or_create(
    username='admin_smartkids',
    defaults={
        'role': User.Role.COURSE_ADMIN,
        'first_name': 'Smart',
        'last_name': 'Admin',
        'company': company,
        'company_name': company.name,
    }
)

if created:
    admin.set_password('admin123')
    admin.save()
    print(f"✅ Админ создан: {admin.username}")
else:
    # Обновляем company если не установлен
    if admin.company != company:
        admin.company = company
        admin.company_name = company.name
        admin.save()
        print(f"✅ Админ обновлен: {admin.username}")
    else:
        print(f"ℹ️ Админ уже существует: {admin.username}")

# Создаем менеджеров
for i in range(2):
    manager, created = User.objects.get_or_create(
        username=f'manager_smartkids_{i+1}',
        defaults={
            'role': User.Role.MANAGER,
            'first_name': f'Manager {i+1}',
            'last_name': 'SmartKids',
            'company': company,
            'company_name': company.name,
        }
    )
    if created:
        manager.set_password('admin123')
        manager.save()
        print(f"✅ Менеджер создан: {manager.username}")

# Создаем 5 курсов (без category и is_active - их нет в модели)
courses_data = [
    {
        'title': 'Английский для детей (4-6 лет)',
        'price': 2500,
        'duration_weeks': 16,
        'description': 'Игровой английский для самых маленьких. Развиваем речь, память и коммуникацию.',
    },
    {
        'title': 'Английский для школьников (7-10 лет)',
        'price': 3000,
        'duration_weeks': 20,
        'description': 'Изучаем грамматику, словарный запас и разговорную речь.',
    },
    {
        'title': 'Программирование для детей (Scratch)',
        'price': 3500,
        'duration_weeks': 12,
        'description': 'Учимся создавать игры и анимации в Scratch.',
    },
    {
        'title': 'Python для детей (10+ лет)',
        'price': 4000,
        'duration_weeks': 24,
        'description': 'Основы программирования на Python. Создаем проекты и игры.',
    },
    {
        'title': 'Логика и математика для детей',
        'price': 2800,
        'duration_weeks': 16,
        'description': 'Развиваем логическое мышление и математические способности.',
    },
]

for cd in courses_data:
    course, created = Course.objects.get_or_create(
        title=cd['title'],
        defaults={
            'price': cd['price'],
            'duration_weeks': cd['duration_weeks'],
            'description': cd['description'],
            'lesson_duration_minutes': 60,
            'schedule': '2 раза в неделю',
        }
    )
    if created:
        course.admins.add(admin)
        print(f"✅ Курс создан: {course.title}")
    else:
        # Обновляем админа
        course.admins.add(admin)
        print(f"ℹ️ Курс уже существует: {course.title}")

# Создаем 10 учителей
teachers_data = [
    ('Айжан', 'Алиева'),
    ('Бакыт', 'Исаков'),
    ('Каныбек', 'Раимов'),
    ('Дилшод', 'Абдыров'),
    ('Эльмира', 'Сатыева'),
    ('Нурзат', 'Усенова'),
    ('Талант', 'Козлов'),
    ('Айсулуу', 'Иванова'),
    ('Жаныбек', 'Петров'),
    ('Гульнара', 'Сидорова'),
]

teachers = []
for idx, (first_name, last_name) in enumerate(teachers_data):
    username = f'teacher_{first_name.lower()}_{last_name.lower()}'
    teacher, created = User.objects.get_or_create(
        username=username,
        defaults={
            'role': User.Role.TEACHER,
            'first_name': first_name,
            'last_name': last_name,
            'company': company,
            'company_name': company.name,
            'phone': f'+996700{100000 + idx:06d}',
        }
    )
    if created:
        teacher.set_password('admin123')
        teacher.save()
        teachers.append(teacher)
        print(f"✅ Учитель создан: {first_name} {last_name}")
    else:
        teachers.append(teacher)
        print(f"ℹ️ Учитель уже существует: {first_name} {last_name}")

# Создаем лендинг
landing, created = LandingPage.objects.get_or_create(
    company=company,
    slug='smart-kids-center-main',
    defaults={
        'title': 'Smart Kids Center',
        'status': LandingPage.Status.ACTIVE,
    }
)

if created:
    print(f"✅ Лендинг создан: {landing.title}")
else:
    print(f"ℹ️ Лендинг уже существует: {landing.title}")
    # Обновляем статус
    landing.status = LandingPage.Status.ACTIVE
    landing.save()

# Создаем секции лендинга
sections_data = [
    {'section_type': 'hero', 'order': 1, 'content': {'title': 'Smart Kids Center', 'subtitle': 'Развитие детей с любовью', 'description': 'Лучший центр развития в Бишкеке'}},
    {'section_type': 'about', 'order': 2, 'content': {'title': 'О нас', 'description': 'Мы работаем с 2015 года и подготовили более 1000 детей'}},
    {'section_type': 'features', 'order': 3, 'content': {'title': 'Почему выбирают нас', 'items': 'Опытные преподаватели\nСовременные методики\nИндивидуальный подход\nУютная атмосфера'}},
    {'section_type': 'course_grid', 'order': 4, 'content': {'title': 'Наши курсы'}},
    {'section_type': 'statistics', 'order': 5, 'content': {'title': 'Наши достижения', 'items': '8+ Лет опыта\n1000+ Выпускников\n10+ Преподавателей\n95% Успешность'}},
    {'section_type': 'testimonials', 'order': 6, 'content': {'title': 'Отзывы родителей', 'items': 'Отличный центр! Дети с удовольствием ходят. - Анна\nПрофессиональные учителя. - Бакыт'}},
    {'section_type': 'faq', 'order': 7, 'content': {'title': 'Частые вопросы', 'items': 'Какой возраст?|4-14 лет\nСколько занятий?|2-3 в неделю\nЕсть ли пробный?|Да, бесплатный'}},
    {'section_type': 'lead_form', 'order': 8, 'content': {'title': 'Записаться на консультацию'}},
    {'section_type': 'contacts', 'order': 9, 'content': {'title': 'Контакты'}},
]

for sd in sections_data:
    section, created = LandingSection.objects.get_or_create(
        page=landing,
        section_type=sd['section_type'],
        order=sd['order'],
        defaults={'content': sd['content']}
    )
    if created:
        print(f"✅ Секция создана: {sd['section_type']}")
    else:
        # Обновляем контент
        section.content = sd['content']
        section.save()
        print(f"ℹ️ Секция обновлена: {sd['section_type']}")

# Создаем 10 студентов
students_data = [
    ('Али', 'Алиев'),
    ('Айша', 'Алиева'),
    ('Бакыт', 'Исаков'),
    ('Дияра', 'Исаева'),
    ('Эмир', 'Раимов'),
    ('Айым', 'Раимова'),
    ('Талант', 'Абдыров'),
    ('Саида', 'Абдырова'),
    ('Каныбек', 'Усенов'),
    ('Нургуль', 'Усенова'),
]

for idx, (first_name, last_name) in enumerate(students_data):
    username = f'student_{first_name.lower()}_{last_name.lower()}'
    student, created = User.objects.get_or_create(
        username=username,
        defaults={
            'role': User.Role.STUDENT,
            'first_name': first_name,
            'last_name': last_name,
            'company': company,
            'company_name': company.name,
            'phone': f'+996701{100000 + idx:06d}',
        }
    )
    if created:
        student.set_password('admin123')
        student.save()
        print(f"✅ Студент создан: {first_name} {last_name}")
    else:
        print(f"ℹ️ Студент уже существует: {first_name} {last_name}")

# Создаем 5 тестовых заявок (leads) для May
for i in range(5):
    lead, created = TrialLead.objects.get_or_create(
        id=i+1,
        defaults={
            'full_name': f'Родитель {i+1}',
            'phone': f'+996702{100000 + i:06d}',
            'company': company,
            'course_interest': 'Английский язык',
            'comment': f'Интересует запись ребенка на курс (тестовая заявка {i+1})',
        }
    )
    if created:
        print(f"✅ Заявка создана: {lead.full_name}")
    else:
        print(f"ℹ️ Заявка уже существует: {lead.full_name}")

print("\n" + "="*50)
print("✅ Все данные для Smart Kids Center созданы!")
print("="*50)
print(f"\nЛогин для входа:")
print(f"  Админ: admin_smartkids / admin123")
print(f"  Менеджер 1: manager_smartkids_1 / admin123")
print(f"  Менеджер 2: manager_smartkids_2 / admin123")
print(f"\nУчителя (10 шт): teacher_... / admin123")
print(f"\nСтуденты (10 шт): student_... / admin123")
print(f"\nЛендинг: http://localhost:3001/ru/public/landing-pages/smart-kids-center-main")
