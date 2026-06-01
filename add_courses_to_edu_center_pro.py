import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Course, Company

# Находим компанию
company = Company.objects.filter(name="Edu Center Pro").first()
if not company:
    print("Ошибка: Компания 'Edu Center Pro' не найдена!")
    exit(1)

print(f"Компания: {company.name} (ID: {company.id})")

# Список из 10 курсов
courses_data = [
    {
        "title": "Английский для начинающих (A1)",
        "price": 2500,
        "duration_weeks": 12,
        "lesson_duration_minutes": 90,
        "description": "Базовый курс английского языка для новичков. Изучение грамматики, лексики и разговорной практики.",
        "schedule": "Пн, Ср, Пт 18:00-19:30"
    },
    {
        "title": "Английский средний уровень (B1)",
        "price": 3000,
        "duration_weeks": 16,
        "lesson_duration_minutes": 90,
        "description": "Развитие навыков общения, расширенная грамматика, подготовка к международным экзаменам.",
        "schedule": "Вт, Чт, Сб 17:00-18:30"
    },
    {
        "title": "Продвинутый английский (B2-C1)",
        "price": 3500,
        "duration_weeks": 20,
        "lesson_duration_minutes": 120,
        "description": "Углубленное изучение языка, подготовка к IELTS/TOEFL, бизнес-английский.",
        "schedule": "Пн, Ср 19:00-21:00"
    },
    {
        "title": "Детский английский (5-8 лет)",
        "price": 2800,
        "duration_weeks": 14,
        "lesson_duration_minutes": 60,
        "description": "Игровой метод обучения английского для детей. Сказки, песни, веселые задания.",
        "schedule": "Сб, Вс 10:00-11:00"
    },
    {
        "title": "Разговорный клуб",
        "price": 1500,
        "duration_weeks": 8,
        "lesson_duration_minutes": 90,
        "description": "Практика разговорного английского на различные темы. Общение с носителями языка.",
        "schedule": "Чт 18:00-19:30"
    },
    {
        "title": "Подготовка к IELTS",
        "price": 4500,
        "duration_weeks": 24,
        "lesson_duration_minutes": 120,
        "description": "Комплексная подготовка к экзамену IELTS. Все разделы: Reading, Writing, Listening, Speaking.",
        "schedule": "Пн, Ср, Пт 17:00-19:00"
    },
    {
        "title": "Бизнес-английский",
        "price": 4000,
        "duration_weeks": 16,
        "lesson_duration_minutes": 90,
        "description": "Английский для бизнеса: переговоры, презентации, деловая переписка.",
        "schedule": "Вт, Чт 19:00-20:30"
    },
    {
        "title": "Английский для путешествий",
        "price": 2000,
        "duration_weeks": 8,
        "lesson_duration_minutes": 60,
        "description": "Базовые фразы и лексика для путешествий. Аэропорт, отель, ресторан, навигация.",
        "schedule": "Сб 11:00-12:00"
    },
    {
        "title": "Английский для IT-специалистов",
        "price": 3800,
        "duration_weeks": 12,
        "lesson_duration_minutes": 90,
        "description": "Специализированный курс для программистов и IT-специалистов. Техническая документация, интервью.",
        "schedule": "Вт, Чт 20:00-21:30"
    },
    {
        "title": "Интенсивный курс (Bootcamp)",
        "price": 6000,
        "duration_weeks": 10,
        "lesson_duration_minutes": 180,
        "description": "Полный погружение в английский язык. 5 дней в неделю, интенсивная практика.",
        "schedule": "Пн-Пт 15:00-18:00"
    },
]

# Создаём курсы
print("\nСоздание курсов...")
created_count = 0
for course_data in courses_data:
    # Проверяем, существует ли курс
    if Course.objects.filter(title=course_data["title"]).exists():
        print(f"  ⏭️  {course_data['title']} - уже существует")
        continue
    
    course = Course.objects.create(**course_data)
    print(f"  ✅ {course.title} - создан (ID: {course.id}, Цена: {course.price} сом)")
    created_count += 1

print(f"\n✅ Успешно создано курсов: {created_count}")
print(f"📊 Всего курсов: {Course.objects.count()}")
