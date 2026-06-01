import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, Course, PublicCourse, JobVacancy, User

# Получаем компанию
company = Company.objects.filter(slug='smart-kids-center').first()
if not company:
    print("❌ Компания не найдена!")
    exit(1)

print(f"🔄 Добавление курсов и вакансий для: {company.name}")
print("="*60)

# Получаем админа
admin = User.objects.filter(username='admin_smartkids').first()
if not admin:
    print("❌ Админ не найден!")
    exit(1)

# 1. Создаем PublicCourse для каждого курса
courses_data = [
    {
        'title': 'Английский для детей (4-6 лет)',
        'description': 'Игровой английский для самых маленьких. Развиваем речь, память и коммуникацию через игры и песни.',
        'price': 2500,
        'duration_weeks': 16,
        'lesson_duration_minutes': 60,
        'level': 'beginner',
    },
    {
        'title': 'Английский для школьников (7-10 лет)',
        'description': 'Изучаем грамматику, словарный запас и разговорную речь. Подготовка к школе и международным экзаменам.',
        'price': 3000,
        'duration_weeks': 20,
        'lesson_duration_minutes': 90,
        'level': 'intermediate',
    },
    {
        'title': 'Программирование для детей (Scratch)',
        'description': 'Учимся создавать игры и анимации в Scratch. Развиваем логическое мышление и креативность.',
        'price': 3500,
        'duration_weeks': 12,
        'lesson_duration_minutes': 90,
        'level': 'beginner',
    },
    {
        'title': 'Python для детей (10+ лет)',
        'description': 'Основы программирования на Python. Создаем проекты, игры и простые приложения.',
        'price': 4000,
        'duration_weeks': 24,
        'lesson_duration_minutes': 90,
        'level': 'intermediate',
    },
    {
        'title': 'Логика и математика для детей',
        'description': 'Развиваем логическое мышление и математические способности через интересные задачи и игры.',
        'price': 2800,
        'duration_weeks': 16,
        'lesson_duration_minutes': 60,
        'level': 'beginner',
    },
]

created_courses = 0
for cd in courses_data:
    # Проверяем существование
    if PublicCourse.objects.filter(title=cd['title'], company=company).exists():
        print(f"ℹ️ PublicCourse уже существует: {cd['title']}")
        continue
    
    # Создаем PublicCourse напрямую
    public_course = PublicCourse(
        title=cd['title'],
        company=company,
        description=cd['description'],
        price=cd['price'],
        duration_weeks=cd['duration_weeks'],
        lesson_duration_minutes=cd['lesson_duration_minutes'],
        is_active=True,
        views=0,
    )
    public_course.save()
    created_courses += 1
    print(f"✅ PublicCourse создан: {cd['title']}")

print(f"\n✅ Всего PublicCourse: {PublicCourse.objects.filter(company=company).count()}")

# 2. Создаем вакансии
jobs_data = [
    {
        'title': 'Преподаватель английского языка',
        'description': 'Требуется преподаватель английского языка для работы с детьми от 4 до 10 лет. Опыт работы от 1 года.',
        'salary_min': 25000,
        'salary_max': 40000,
        'city': 'Бишкек',
        'is_active': True,
    },
    {
        'title': 'Преподаватель программирования',
        'description': 'Ищем преподавателя по программированию (Scratch, Python) для детей. Знание современных методик преподавания.',
        'salary_min': 30000,
        'salary_max': 50000,
        'city': 'Бишкек',
        'is_active': True,
    },
    {
        'title': 'Методист',
        'description': 'Разработка учебных программ и методических материалов для детских курсов.',
        'salary_min': 20000,
        'salary_max': 35000,
        'city': 'Бишкек',
        'is_active': True,
    },
    {
        'title': 'Менеджер по продажам',
        'description': 'Консультация родителей, продажа курсов, ведение базы клиентов. Опыт в продажах образования приветствуется.',
        'salary_min': 15000,
        'salary_max': 30000,
        'city': 'Бишкек',
        'is_active': True,
    },
]

created_jobs = 0
for jd in jobs_data:
    # Проверяем существование
    if JobVacancy.objects.filter(title=jd['title'], company=company).exists():
        print(f"ℹ️ Вакансия уже существует: {jd['title']}")
        continue
    
    job = JobVacancy(
        title=jd['title'],
        company=company,
        description=jd['description'],
        salary_min=jd['salary_min'],
        salary_max=jd['salary_max'],
        city=jd['city'],
        is_active=jd['is_active'],
        views=0,
    )
    job.save()
    created_jobs += 1
    print(f"✅ Вакансия создана: {jd['title']}")

print(f"\n✅ Всего вакансий: {JobVacancy.objects.filter(company=company).count()}")

# 3. Итоговая статистика
print("\n" + "="*60)
print("ИТОГОВАЯ СТАТИСТИКА:")
print("="*60)
print(f"Компания: {company.name}")
print(f"PublicCourse: {PublicCourse.objects.filter(company=company).count()}")
print(f"JobVacancy: {JobVacancy.objects.filter(company=company).count()}")

print("\n✅ Все курсы и вакансии добавлены!")
print("\nПроверьте в разделе 'Мои материалы' после входа как менеджер.")