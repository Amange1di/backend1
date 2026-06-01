import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from core.models import (
    User, Company, Student, Group, Course, Task, TrialLead, 
    Attendance, Payment, Auditorium, HomeworkTask, HomeworkSubmission,
    CompanyBalance, Transaction, PromoCode, TaskLead as TaskLeadModel
)
from django.utils import timezone
from datetime import date, timedelta, datetime
import random
import hashlib

# === РЕАЛИСТИЧНЫЕ ДАННЫЕ ===

KYRGYZ_FIRST_NAMES_M = [
    'Айбек', 'Бакыт', 'Данияр', 'Эркін', 'Азамат', 'Талант', 'Каныбек', 'Бекзат', 
    'Алтынбек', 'Сабыр', 'Нурлан', 'Аскар', 'Бекайдар', 'Курманбек', 'Жаныш',
    'Төлөн', 'Айдар', 'Бекей', 'Дуйшен', 'Эркінбек', 'Касым', 'Мурат', 'Равшан',
    'Бердибек', 'Азаматбек', 'Турат', 'Жоомарт', 'Самат', 'Алмат', 'Бакытжан',
    'Арстан', 'Бекболот', 'Данияр', 'Алишер', 'Алпарслан', 'Тайыр', 'Курман',
    'Нурисмаил', 'Айтор', 'Бекумар', 'Даниярбек', 'Айпери', 'Кенжебек', 'Төлөбай'
]

KYRGYZ_FIRST_NAMES_F = [
    'Айгуль', 'Нурезим', 'Гүлнур', 'Айпери', 'Бакытгүл', 'Төлөгөн', 'Каныкей', 
    'Айжамал', 'Нурислам', 'Гүлайым', 'Бакытзат', 'Айбарчы', 'Дилара', 'Эркими',
    'Айзада', 'Бактыгүл', 'Нургуль', 'Айжаныл', 'Гүлбарчын', 'Талантгүл', 'Камила',
    'Айсулуу', 'Нурия', 'Гүлмира', 'Бакыткуль', 'Айгерим', 'Дания', 'Мадина', 'Фарида',
    'Гульназ', 'Айзат', 'Нурания', 'Гүлзат', 'Айсылуу', 'Бактыгүл', 'Кундуз',
    'Айгүл', 'Нуржан', 'Гүлай', 'Айчүрөк', 'Дилназ', 'Айбарчы', 'Бактынай'
]

KYRGYZ_LAST_NAMES = [
    'Алиев', 'Каримов', 'Исаков', 'Усенов', 'Асанов', 'Джеенбеков', 'Атабаев', 
    'Кожошев', 'Мамытов', 'Султанов', 'Раимов', 'Токтогазиев', 'Абдыраков', 
    'Бекманбетов', 'Касымалиев', 'Эшенкулов', 'Турсунбаев', 'Ибраимов', 'Алимурадов',
    'Садыков', 'Жумабеков', 'Омошев', 'Уразов', 'Кожобеков', 'Абдыкаимов',
    'Байгазиев', 'Койчубаев', 'Мамытов', 'Алымкулов', 'Асанкулов', 'Шералиев',
    'Ажигулов', 'Кожокуроев', 'Омошбаев', 'Токтоналиев', 'Абдырахманов'
]

COMPANY_NAMES = [
    'Turar Language Center', 'Bilim Khan', 'Alpamys Education', 'English Pro',
    'Bilim Ordo', 'Nur Medres', 'Rahmat Education', 'Alem School',
]

COURSE_TITLES = [
    ('Английский язык', ['English for Beginners', 'Intermediate English', 'Advanced English', 'IELTS Preparation', 'TOEFL Prep', 'Business English', 'Speaking Club', 'Kids English', 'English Grammar Master', 'Conversation Skills']),
    ('IT Разработка', ['Python Development', 'JavaScript Fullstack', 'Web Design', 'Mobile Development', 'Data Science', 'Machine Learning', 'Java Basics', 'Frontend React', 'Backend Django', 'DevOps Fundamentals']),
    ('Кыргызский язык', ['Кыргызский для начинающих', 'Кыргызский средний уровень', 'Кыргызский продвинутый', 'Кыргызский для иностранцев', 'Деловой кыргызский', 'Кыргызская литература', 'Грамматика кыргызского', 'Разговорный кыргызский', 'Кыргызский для бизнеса', 'Подготовка к экзаменам']),
    ('Программирование', ['C++ Programming', 'C# Development', 'PHP Laravel', 'Go Language', 'Rust Basics', 'Kotlin Android', 'Swift iOS', 'Vue.js Framework', 'Angular Development', 'Node.js Backend']),
    ('Дизайн и творчество', ['Графический дизайн', 'Web Design UI/UX', '3D Моделирование', 'Анимация', 'Фотография', 'Видеомонтаж', 'Иллюстрация', 'Логотип и брендинг', 'Motion Design', 'Creative Writing']),
    ('Бизнес и финансы', ['Основы предпринимательства', 'Бухгалтерия', 'Маркетинг', 'Менеджмент', 'Финансовый анализ', 'Бизнес-планирование', 'Продажи и переговоры', 'Лидерство', 'Стратегическое планирование', 'Экономика предприятия']),
    ('Рисование и искусство', ['Основы рисунка', 'Живопись акварелью', 'Живопись маслом', 'Акварельный пейзаж', 'Портретная живопись', 'Анатомия для художников', 'Композиция', 'Цветоведение', 'Искусство Востока', 'Современное искусство']),
    ('Музыка', ['Гитара для начинающих', 'Пианино', 'Вокал', 'Синтезатор', 'Ударные инструменты', 'Скрипка', 'Теория музыки', 'Сочинение музыки', 'Джазовая импровизация', 'Эстрадное пение']),
    ('Спорт и фитнес', ['Йога', 'Пилатес', 'Функциональный тренинг', 'Кроссфит', 'Бокс', 'Танцы', 'Плавание', 'Бодибилдинг', 'Фитнес для беременных', 'Детская гимнастика']),
    ('Языковые курсы', ['Немецкий язык', 'Французский язык', 'Турецкий язык', 'Китайский язык', 'Арабский язык', 'Испанский язык', 'Итальянский язык', 'Японский язык', 'Корейский язык', 'Хинди']),
]

SCHEDULE_DAYS = ['Пн, Ср, Пт', 'Вт, Чт', 'Пн, Вт, Чт, Пт', 'Сб, Вс', 'Вт, Чт, Вс', 'Пн, Ср, Пт, Вс']
SCHEDULE_TIMES = ['10:00', '12:00', '14:00', '16:00', '18:00', '19:00']

PRICES = [5000, 6000, 7000, 8000, 9000, 10000, 12000, 15000]
DURATIONS = [12, 16, 20, 24, 28, 32]


def generate_full_name():
    """Генерирует реалистичное киргизское ФИО"""
    if random.random() > 0.5:
        return random.choice(KYRGYZ_FIRST_NAMES_M), random.choice(KYRGYZ_LAST_NAMES)
    else:
        return random.choice(KYRGYZ_FIRST_NAMES_F), random.choice(KYRGYZ_LAST_NAMES)


def generate_phone():
    """Генерирует реалистичный номер телефона"""
    prefixes = ['555', '500', '501', '502', '550', '551', '700', '701', '770', '771']
    prefix = random.choice(prefixes)
    number = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return f'+996{prefix}{number}'


def generate_telegram():
    """Генерирует Telegram username"""
    names = ['alex', 'dima', 'max', 'sergey', 'anna', 'maria', 'elena', 'dasha', 
             'ali', 'bakyt', 'guzal', 'aygul', 'nur', 'islam', 'kamila', 'azamat']
    name = random.choice(names)
    num = random.randint(100, 9999)
    return f'@{name}{num}'


print('=' * 80)
print('ГЕНЕРАЦИЯ РЕАЛИСТИЧНЫХ ТЕСТОВЫХ ДАННЫХ')
print('=' * 80)

# Удаляем старые тестовые данные (опционально)
if input('\nУдалить старые тестовые данные? (y/n): ').lower() == 'y':
    print('Удаление старых данных...')
    HomeworkSubmission.objects.all().delete()
    HomeworkTask.objects.all().delete()
    TaskLeadModel.objects.all().delete()
    TrialLead.objects.all().delete()
    Task.objects.all().delete()
    Payment.objects.all().delete()
    Attendance.objects.all().delete()
    Group.objects.all().delete()
    Student.objects.all().delete()
    Course.objects.all().delete()
    Auditorium.objects.all().delete()
    Transaction.objects.all().delete()
    CompanyBalance.objects.all().delete()
    Company.objects.all().delete()
    User.objects.exclude(username='superadmin').delete()
    print('Старые данные удалены.')

# === СОЗДАНИЕ СУПЕР-АДМИНА ===
if not User.objects.filter(username='superadmin').exists():
    superadmin = User.objects.create_superuser(
        username='superadmin',
        email='superadmin@eduosho.kg',
        password='superadmin123',
        first_name='Айбек',
        last_name='Алиев',
        phone='+996555123456',
        telegram='@superadmin_edu',
    )
    print('\n✅ Супер-админ создан: superadmin / superadmin123')
else:
    superadmin = User.objects.get(username='superadmin')
    print('\nℹ️ Супер-админ уже существует')

# === СОЗДАНИЕ ПРОМОКОДОВ ===
promo_codes = [
    {'code': 'START2026', 'value': 100, 'active': True},
    {'code': 'EDU500', 'value': 500, 'active': True},
    {'code': 'WELCOME200', 'value': 200, 'active': True},
    {'code': 'NEWYEAR1000', 'value': 1000, 'active': False},
]

for promo_data in promo_codes:
    if not PromoCode.objects.filter(code=promo_data['code']).exists():
        PromoCode.objects.create(
            code=promo_data['code'],
            reward_value=promo_data['value'],
            reward_type=PromoCode.RewardType.COINS,
            max_usages=100,
            is_active=promo_data['active'],
            created_by=superadmin,
            expiry_date=timezone.now() + timedelta(days=365)
        )

print(f'✅ Создано промокодов: {PromoCode.objects.count()}')

total_students = 0
total_groups = 0
total_courses = 0
total_teachers = 0
total_managers = 0
total_tasks = 0
total_leads = 0
total_payments = 0
total_homework = 0

for company_idx, company_name in enumerate(COMPANY_NAMES, 1):
    print(f'\n{"=" * 60}')
    print(f'🏢 КОМПАНИЯ {company_idx}/4: {company_name}')
    print(f'{"=" * 60}')
    
    # Определяем категорию компании
    if 'English' in company_name or 'Language' in company_name:
        category = 'languages'
        city = random.choice(['Бишкек', 'Ош', 'Онлайн'])
        course_category_idx = 0
    elif 'Code' in company_name or 'Tech' in company_name:
        category = 'it'
        city = random.choice(['Бишкек', 'Онлайн'])
        course_category_idx = 1
    elif 'Smart' in company_name or 'Kids' in company_name:
        category = 'sports'
        city = random.choice(['Джалал-Абад', 'Бишкек'])
        course_category_idx = 8
    elif 'Future' in company_name:
        category = 'languages'
        city = 'Нарын'
        course_category_idx = 0
    elif 'Hub' in company_name:
        category = 'languages'
        city = 'Каракол'
        course_category_idx = 9
    elif 'Creative' in company_name:
        category = 'music'
        city = 'Талас'
        course_category_idx = 7
    elif 'Alpamys' in company_name:
        category = 'it'
        city = 'Бишкек'
        course_category_idx = 3
    elif 'English Pro' in company_name:
        category = 'languages'
        city = 'Бишкек'
        course_category_idx = 0
    elif 'Bilim Ordo' in company_name:
        category = 'languages'
        city = 'Ош'
        course_category_idx = 2
    elif 'Nur Medres' in company_name:
        category = 'languages'
        city = 'Джалал-Абад'
        course_category_idx = 2
    elif 'Rahmat Education' in company_name:
        category = 'it'
        city = 'Бишкек'
        course_category_idx = 1
    elif 'Alem School' in company_name:
        category = 'sports'
        city = 'Каракол'
        course_category_idx = 8
    else:
        category = 'languages'
        city = 'Бишкек'
        course_category_idx = 0
    
    # Создаём Course Admin с реалистичным именем
    admin_username = company_name.lower().replace(' ', '_')
    if User.objects.filter(username=admin_username).exists():
        admin_user = User.objects.get(username=admin_username)
    else:
        first_name, last_name = generate_full_name()
        admin_user = User.objects.create_user(
            username=admin_username,
            email=f'{admin_username}@eduosho.kg',
            password='password123',
            role=User.Role.COURSE_ADMIN,
            first_name=first_name,
            last_name=last_name,
            phone=generate_phone(),
            telegram=generate_telegram(),
            salary_rate=random.choice([30000, 40000, 50000, 60000]),
        )
    
    # Создаём компанию
    if Company.objects.filter(name=company_name).exists():
        company = Company.objects.get(name=company_name)
        company.owner = admin_user
        company.category = category
        company.city = city
        company.save()
    else:
        company = Company.objects.create(
            name=company_name,
            owner=admin_user,
            category=category,
            city=city,
            district=random.choice(['Центральный', 'Первомайский', 'Ленинский', 'Октябрьский', 'Микрорайон']),
            phone=generate_phone(),
            telegram=generate_telegram(),
            description=f'Образовательный центр {company_name} предлагает качественные курсы для всех возрастов.',
            rating=round(random.uniform(4.0, 5.0), 1),
            reviews_count=random.randint(10, 100),
            is_active=True,
        )
    
    admin_user.company = company
    admin_user.company_name = company.name
    admin_user.max_managers = 10
    admin_user.save()
    
    print(f'   ✅ Компания: {company.name} ({city}, {category})')
    print(f'   👔 Course Admin: {admin_user.first_name} {admin_user.last_name}')
    
    # Создаём 10 учителей с реалистичными именами
    teachers = []
    teachers_created = 0
    for t_idx in range(10):
        teacher_username = f'{admin_username}_teacher_{t_idx}'
        if User.objects.filter(username=teacher_username).exists():
            # Загружаем существующего учителя
            teacher = User.objects.get(username=teacher_username)
            teachers.append(teacher)
        else:
            first_name, last_name = generate_full_name()
            teacher = User.objects.create_user(
                username=teacher_username,
                email=f'{teacher_username}@eduosho.kg',
                password='password123',
                role=User.Role.TEACHER,
                first_name=first_name,
                last_name=last_name,
                company=company,
                company_name=company.name,
                phone=generate_phone(),
                telegram=generate_telegram(),
                salary_rate=random.choice([15000, 20000, 25000, 30000]),
                working_hours=random.choice(['09:00-18:00', '10:00-19:00', '14:00-23:00']),
            )
            teachers.append(teacher)
            teachers_created += 1
            total_teachers += 1
    
    print(f'   ✅ Учителей: {len(teachers)} (создано новых: {teachers_created})')
    
    # Создаём менеджеров (3-4 на компанию)
    managers = []
    managers_created = 0
    num_managers = random.randint(3, 4)
    for m_idx in range(num_managers):
        manager_username = f'{admin_username}_manager_{m_idx}'
        if User.objects.filter(username=manager_username).exists():
            manager = User.objects.get(username=manager_username)
            managers.append(manager)
        else:
            first_name, last_name = generate_full_name()
            manager = User.objects.create_user(
                username=manager_username,
                email=f'{manager_username}@eduosho.kg',
                password='password123',
                role=User.Role.MANAGER,
                first_name=first_name,
                last_name=last_name,
                company=company,
                company_name=company.name,
                phone=generate_phone(),
                telegram=generate_telegram(),
                salary_rate=random.choice([12000, 15000, 18000]),
            )
            manager.created_by = admin_user
            manager.save()
            managers.append(manager)
            managers_created += 1
            total_managers += 1
    
    print(f'   ✅ Менеджеров: {len(managers)} (создано новых: {managers_created})')
    
    # Создаём 2-3 Task Lead'ов (менеджеров с особыми правами)
    task_leads = []
    task_lead_users = []
    task_leads_created = 0
    num_task_leads = random.randint(2, 3)
    for tl_idx in range(num_task_leads):
        task_lead_username = f'{admin_username}_tasklead_{tl_idx}'
        if User.objects.filter(username=task_lead_username).exists():
            task_lead_user = User.objects.get(username=task_lead_username)
            task_lead_users.append(task_lead_user)
            # Проверяем есть ли профиль Task Lead
            task_lead_profile = TaskLeadModel.objects.filter(user=task_lead_user, company=company).first()
            if task_lead_profile:
                task_leads.append(task_lead_profile)
        else:
            first_name, last_name = generate_full_name()
            task_lead_user = User.objects.create_user(
                username=task_lead_username,
                email=f'{task_lead_username}@eduosho.kg',
                password='password123',
                role=User.Role.MANAGER,
                first_name=first_name,
                last_name=last_name,
                company=company,
                company_name=company.name,
                phone=generate_phone(),
                telegram=generate_telegram(),
                salary_rate=random.choice([25000, 30000, 35000]),
            )
            task_lead_user.created_by = admin_user
            task_lead_user.save()
            task_lead_users.append(task_lead_user)
            
            # Создаём профиль Task Lead
            task_lead = TaskLeadModel.objects.create(
                user=task_lead_user,
                company=company,
                role=random.choice([TaskLeadModel.Role.TASK_LEAD, TaskLeadModel.Role.TEAM_LEAD]),
                team_size=random.randint(2, 5),
                max_tasks=random.randint(30, 50),
                performance_score=round(random.uniform(70, 95), 2),
                responsibilities=random.choice([
                    'Управление командой менеджеров, контроль задач',
                    'Координация работы отдела продаж',
                    'Контроль выполнения KPI команды',
                    'Обучение и наставничество менеджеров',
                ]),
                target_metrics={
                    'conversion_rate': round(random.uniform(20, 40), 1),
                    'customer_satisfaction': round(random.uniform(4.0, 5.0), 1),
                    'tasks_completed': random.randint(80, 100),
                },
                is_active=True,
            )
            task_leads.append(task_lead)
            task_leads_created += 1
            total_managers += 1
    
    if task_leads:
        print(f'   ✅ Task Lead: {len(task_leads)} (создано новых: {task_leads_created})')
    
    # Создаём 5-7 аудиторий
    for a_idx in range(random.randint(5, 7)):
        Auditorium.objects.create(
            name=f'Аудитория {a_idx + 1}',
            number=str(101 + a_idx),
            company=company,
            company_name=company.name,
        )
    print(f'   ✅ Создано аудиторий: {Auditorium.objects.filter(company=company).count()}')
    
    # Создаём 10 курсов
    courses = []
    courses_created = 0
    
    for c_idx in range(10):
        category_name, titles = COURSE_TITLES[course_category_idx]
        title = titles[c_idx % len(titles)]
        
        full_title = f'{title} - {company_name}'
        
        if Course.objects.filter(title=full_title).exists():
            course = Course.objects.get(title=full_title)
            courses.append(course)
        else:
            course = Course.objects.create(
                title=full_title,
                price=random.choice(PRICES),
                duration_weeks=random.choice(DURATIONS),
                lesson_duration_minutes=random.choice([60, 90, 120]),
                description=f'Профессиональный курс {title} в образовательном центре {company_name}. '
                           f'Опытные преподаватели, современное оборудование, индивидуальный подход.',
                schedule=random.choice(SCHEDULE_DAYS),
                is_promoted=c_idx < 3,  # Первые 3 курса - TOP
            )
            course.admins.add(admin_user)
            courses.append(course)
            courses_created += 1
            total_courses += 1
    
    print(f'   ✅ Курсов: {len(courses)} (создано новых: {courses_created})')
    
    # Создаём 1 группу на каждый курс
    groups = []
    groups_created = 0
    for g_idx, course in enumerate(courses):
        teacher = teachers[g_idx % len(teachers)]
        
        if not teacher.teaching_courses.filter(id=course.id).exists():
            teacher.teaching_courses.add(course)
        
        group_name = f'{course.title.split(" - ")[0]} - {company_name.split()[0]} - Группа'
        
        if Group.objects.filter(name=group_name).exists():
            group = Group.objects.get(name=group_name)
            groups.append(group)
        else:
            auditorium = Auditorium.objects.filter(company=company).order_by('?').first()
            group = Group.objects.create(
                name=group_name,
                course=course,
                teacher=teacher,
                company=company,
                company_name=company.name,
                schedule_days=random.choice(SCHEDULE_DAYS),
                schedule_time=random.choice(SCHEDULE_TIMES),
                auditorium=auditorium,
                lessons_count=random.randint(24, 48),
                start_date=date.today() - timedelta(days=random.randint(10, 100)),
                end_date=date.today() + timedelta(days=random.randint(50, 200)),
                is_login_allowed=True,
            )
            groups.append(group)
            groups_created += 1
            total_groups += 1
    
    print(f'   ✅ Групп: {len(groups)} (создано новых: {groups_created})')
    
    # Создаём студентов для каждой группы (ровно 7 студентов на группу)
    company_students = []
    students_created = 0
    
    for group in groups:
        # Загружаем существующих студентов группы
        existing_students = list(group.students.all())
        target_count = 7  # Ровно 7 студентов на группу
        current_count = len(existing_students)
        
        group_students = existing_students.copy()
        
        # Создаём недостающих студентов
        for s_idx in range(current_count, target_count):
            first_name, last_name = generate_full_name()
            
            # Генерируем уникальный номер телефона
            while True:
                phone = generate_phone()
                if not Student.objects.filter(phone=phone).exists():
                    break
            
            # Создаём пользователя для студента (опционально)
            user = None
            if random.random() > 0.3:  # 70% студентов имеют учётную запись
                user_username = f'std_{company_idx}_{len(company_students)}_{s_idx}'
                if not User.objects.filter(username=user_username).exists():
                    user = User.objects.create_user(
                        username=user_username,
                        password='student123',
                        role=User.Role.STUDENT,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        company=company,
                        company_name=company.name,
                    )
            
            student = Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                telegram=generate_telegram(),
                company=company,
                company_name=company.name,
                primary_course=group.course,
                notes=random.choice([
                    'Хороший студент, активно участвует',
                    'Нужно больше практиковаться',
                    'Отличная посещаемость',
                    'Требуется дополнительная помощь',
                    '',
                    'Рекомендован родственниками',
                    'Заинтересован в карьерном росте',
                ]),
            )
            group.students.add(student)
            group_students.append(student)
            company_students.append(student)
            students_created += 1
            total_students += 1
        
        # Создаём записи посещаемости (последние 30 дней)
        for day_offset in range(30):
            lesson_date = date.today() - timedelta(days=day_offset * 3)
            for student in group_students:
                # Разные уровни посещаемости
                attend_roll = random.random()
                if attend_roll > 0.15:  # 85% посещаемость в среднем
                    status = Attendance.Status.PRESENT
                elif attend_roll > 0.10:  # 5% пропусков по болезни
                    status = Attendance.Status.EXCUSED
                else:  # 10% пропусков без причины
                    status = Attendance.Status.ABSENT
                
                Attendance.objects.get_or_create(
                    group=group,
                    student=student,
                    date=lesson_date,
                    defaults={'status': status}
                )
    
    print(f'   ✅ Студентов: {len(company_students)} (создано новых: {students_created})')
    
    # Создаём платежи (разная система оплаты)
    # Каждый студент может иметь несколько платежей (ежемесячные)
    for student in company_students:
        # Определяем общую сумму курса
        course = student.primary_course
        if course:
            total_price = float(course.price)
        else:
            total_price = random.choice(PRICES)
        
        # Студент платит частями (например, 4 платежа)
        num_payments = random.randint(2, 5)
        payment_amount = total_price / num_payments
        
        paid_count = 0
        for p_idx in range(num_payments):
            # 80% платят вовремя, 20% имеют задолженность
            if random.random() > 0.2:
                status = Payment.Status.PAID
                paid_at = date.today() - timedelta(days=(num_payments - p_idx) * 30)
                paid_count += 1
            else:
                status = Payment.Status.DEBT
                paid_at = date.today()
            
            Payment.objects.create(
                student=student,
                group=student.groups.first(),
                amount=payment_amount,
                status=status,
                paid_at=paid_at,
            )
            total_payments += 1
        
        # Создаём транзакцию в системе баланса компании
        if paid_count > 0:
            CompanyBalance.objects.get_or_create(
                company=company,
                company_name=company.name,
                defaults={'balance': 50000}
            )
            balance = CompanyBalance.objects.get(company=company)
            total_paid = payment_amount * paid_count
            balance.add_coins(int(total_paid), f'Оплата студентом: {student.first_name} {student.last_name}')
    
    print(f'   ✅ Создано платежей: {Payment.objects.filter(student__company=company).count()}')
    
    # Создаём домашние задания
    homework_count = 0
    for group in groups[:8]:  # 8 групп имеют домашние задания
        for task_idx in range(random.randint(3, 6)):
            hw_task = HomeworkTask.objects.create(
                group=group,
                teacher=group.teacher,
                company=company,
                company_name=company.name,
                title=f'Задание {task_idx + 1}: {group.name}',
                description=random.choice([
                    'Выполнить упражнения 1-10 на стр. 45',
                    'Написать эссе на тему "Моя будущая профессия"',
                    'Создать проект по материалам урока',
                    'Подготовить презентацию на 5 минут',
                    'Решить задачи из главы 3',
                    'Просмотреть видеоурок и ответить на вопросы',
                    'Подготовиться к контрольной работе',
                ]),
                lesson_number=task_idx + 1,
                deadline=timezone.now() + timedelta(days=random.randint(3, 14)),
                is_published=True,
                task_type=random.choice([HomeworkTask.TaskType.HOMEWORK, HomeworkTask.TaskType.QUIZ, HomeworkTask.TaskType.PROJECT]),
            )
            
            # Создаём ответы от студентов (разные статусы)
            for student in group.students.all():
                if random.random() > 0.2:  # 80% сдают домашку
                    submission_status = random.choices(
                        [HomeworkSubmission.Status.PENDING, HomeworkSubmission.Status.REVIEWED, HomeworkSubmission.Status.REJECTED],
                        weights=[20, 70, 10]
                    )[0]
                    
                    if submission_status == HomeworkSubmission.Status.REVIEWED:
                        grade = random.randint(65, 100)
                        comment = random.choice([
                            'Отличная работа! Продолжай в том же духе.',
                            'Хороший результат, но есть над чем работать.',
                            'Требует доработки. Обратите внимание на замечания.',
                            'Очень хорошо! Небольшая ошибка в последнем задании.',
                            'Молодец! Все задания выполнены правильно.',
                        ])
                    elif submission_status == HomeworkSubmission.Status.REJECTED:
                        grade = random.randint(40, 64)
                        comment = random.choice([
                            'Нужно переделать. Основные ошибки: ...',
                            'Не соответствует требованиям. Пересмотрите задание.',
                            'Неполное выполнение. Добавьте недостающие части.',
                        ])
                    else:
                        grade = None
                        comment = ''
                    
                    HomeworkSubmission.objects.create(
                        task=hw_task,
                        student=student,
                        status=submission_status,
                        grade=grade,
                        teacher_comment=comment,
                    )
                    homework_count += 1
    
    total_homework += homework_count
    print(f'   ✅ Создано домашних заданий и ответов: {homework_count}')
    
    # Создаём задачи для менеджеров и Task Lead'ов
    tasks_created = 0
    for task_idx in range(random.randint(5, 8)):
        if managers or task_lead_users:
            all_managers = managers + task_lead_users
            task_lead = random.choice(task_leads) if task_leads else None
            
            task = Task.objects.create(
                title=random.choice([
                    'Обработать новые заявки с сайта',
                    'Связаться с родителями студентов',
                    'Подготовить отчёт по посещаемости',
                    'Организовать родительское собрание',
                    'Проверить оплату студентов',
                    'Подготовить материалы для открытого урока',
                    'Связаться с потенциальными клиентами',
                    'Организовать экскурсию для студентов',
                    'Подготовить сертификаты об окончании курса',
                    'Обновить информацию на сайте',
                ]),
                description='Выполнить задачу в установленный срок',
                assigned_to=random.choice(all_managers),
                task_lead=task_lead,
                company=company,
                company_name=company.name,
                due_date=date.today() + timedelta(days=random.randint(1, 14)),
                status=random.choices(
                    [Task.Status.PENDING, Task.Status.IN_PROGRESS, Task.Status.COMPLETED],
                    weights=[30, 40, 30]
                )[0],
                priority=random.choices(
                    [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH],
                    weights=[20, 50, 30]
                )[0],
            )
            
            # Если задача выполнена, добавляем дату завершения
            if task.status == Task.Status.COMPLETED:
                task.completed_at = timezone.now() - timedelta(days=random.randint(1, 5))
                task.save()
            
            tasks_created += 1
            total_tasks += 1
    
    print(f'   ✅ Задач: {Task.objects.filter(company=company).count()} (создано новых: {tasks_created})')
    
    # Создаём Test Drive Leads (15-25 на компанию)
    leads_created = 0
    target_leads = random.randint(15, 25)
    current_leads = TrialLead.objects.filter(company=company).count()
    
    for lead_idx in range(current_leads, target_leads):
        first_name, last_name = generate_full_name()
        
        # Генерируем уникальный телефон
        while True:
            phone = generate_phone()
            if not TrialLead.objects.filter(phone=phone, company=company).exists():
                break
        
        TrialLead.objects.create(
            full_name=f'{first_name} {last_name}',
            phone=phone,
            age=random.randint(14, 50),
            course_interest=random.choice([c.title for c in courses]),
            trial_attended=random.random() > 0.3,  # 70% приходят на пробный
            status=random.choices(
                [
                    TrialLead.Status.NEW,
                    TrialLead.Status.CONTACTED,
                    TrialLead.Status.TRIAL_SCHEDULED,
                    TrialLead.Status.ATTENDED,
                    TrialLead.Status.NOT_ATTENDED,
                    TrialLead.Status.CONVERTED
                ],
                weights=[15, 20, 15, 20, 10, 20]
            )[0],
            trial_date=date.today() - timedelta(days=random.randint(0, 30)),
            source=random.choice(['Instagram', 'Facebook', 'Google', 'Word of mouth', 'Telegram', 'Website', 'Radio']),
            company=company,
            company_name=company.name,
            comment=random.choice([
                'Интересуется карьерой в IT',
                'Хочет улучшить английский для работы',
                'Ищет курсы для ребёнка',
                'Готов начать обучение сразу',
                'Нужна консультация по расписанию',
                '',
            ]),
            converted_to_student=random.random() > 0.6,  # 40% конверсия
            payment_status=random.choices(
                [TrialLead.PaymentStatus.NOT_PAID, TrialLead.PaymentStatus.PAID, TrialLead.PaymentStatus.PARTIAL],
                weights=[40, 45, 15]
            )[0],
        )
        leads_created += 1
        total_leads += 1
    
    print(f'   ✅ Trial Lead: {TrialLead.objects.filter(company=company).count()} (создано новых: {leads_created})')

# Создаём балансы для всех компаний
for company in Company.objects.all():
    balance, created = CompanyBalance.objects.get_or_create(
        company=company,
        company_name=company.name,
        defaults={'balance': random.randint(30000, 150000)}
    )
    if not created:
        balance.balance = random.randint(30000, 150000)
        balance.save()

# Создаём общие промокоды для системы

print('\n' + '=' * 80)
print('📊 ИТОГОВАЯ СТАТИСТИКА')
print('=' * 80)
print(f'🏢 Компаний: {Company.objects.count()}')
print(f'👑 Супер-админов: {User.objects.filter(role=User.Role.SUPER_ADMIN).count()}')
print(f'👔 Course Admins: {User.objects.filter(role=User.Role.COURSE_ADMIN).count()}')
print(f'👨‍🏫 Учителей: {total_teachers}')
print(f'👥 Менеджеров (включая Task Lead): {total_managers}')
print(f'📚 Курсов: {total_courses}')
print(f'📋 Групп: {total_groups}')
print(f'🎓 Студентов: {total_students}')
print(f'✅ Задач: {total_tasks}')
print(f'🎯 Trial Lead: {total_leads}')
print(f'💰 Платежей: {total_payments}')
print(f'📝 Домашних заданий: {total_homework}')
print(f'💳 Балансов компаний: {CompanyBalance.objects.count()}')
print(f'💵 Транзакций: {Transaction.objects.count()}')
print(f'🎟️ Промокодов: {PromoCode.objects.count()}')
print('=' * 80)

print('\n🔐 Логин для доступа:')
print('   👑 Супер-админ: superadmin / superadmin123')
print('   👔 Course Admin: <название_компании> / password123')
print('   👨‍🏫 Учитель: <company>_teacher_0 / password123')
print('   👥 Менеджер: <company>_manager_0 / password123')
print('   🎓 Студент: <любой логин> / student123')

print('\n✅ Генерация реалистичных тестовых данных завершена!')
print('\n📝 Примечания:')
print('   - Все ФИО реалистичные (киргизские и русские имена)')
print('   - Система посещаемости: последние 30 дней занятий')
print('   - Система оплаты: частичная оплата с задолженностями')
print('   - Домашние задания: с проверкой и оценками')
print('   - Trial Lead: полная воронка от заявки до оплаты')
print('   - Task Lead: менеджеры с повышенными правами')
print('   - Баланс компаний: eduCoins с историей транзакций')