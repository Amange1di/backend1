"""
Скрипт для создания лендинга Turar Language Center
со всеми доступными компонентами/секциями.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, LandingPage, LandingSection

# Найти компанию
company = Company.objects.filter(name="Turar Language Center").first()
if not company:
    print("❌ Компания 'Turar Language Center' не найдена!")
    exit(1)

print(f"✅ Найдена компания: {company.name} (slug: {company.slug})")

# Удалить существующие лендинги этой компании (чтобы пересоздать)
existing = LandingPage.objects.filter(company=company)
if existing.exists():
    print(f"🗑 Удаляю {existing.count()} существующий(их) лендинг(ов)...")
    existing.delete()

# Создать лендинг
landing = LandingPage(
    title="Turar Language Center — Изучайте языки с нами",
    slug=f"turar-language-center-{company.id}",
    company=company,
    status=LandingPage.Status.ACTIVE,
)
landing.save()
print(f"✅ Лендинг создан: {landing.slug} (ID: {landing.id})")

# Все доступные секции
sections_data = [
    # 1. HERO — Главный экран
    {
        "section_type": "hero",
        "order": 0,
        "content": {
            "title": "Turar Language Center",
            "subtitle": "Откройте мир языков вместе с нами!",
            "description": "Профессиональные курсы английского, русского, кыргызского и других языков. Опытные преподаватели, современные методики, комфортная атмосфера.",
            "cta_text": "Записаться на пробный урок",
            "cta_link": "#lead_form",
            "background_color": "#1a1a2e",
            "text_color": "#ffffff",
        }
    },
    # 2. ABOUT — О нас
    {
        "section_type": "about",
        "order": 1,
        "content": {
            "title": "О нашем центре",
            "description": "Turar Language Center — это современный языковой центр в городе Ош. Мы помогаем студентам всех возрастов свободно общаться на иностранных языках. Наши преподаватели — сертифицированные специалисты с международными дипломами и многолетним опытом работы. Мы используем коммуникативную методику, которая позволяет заговорить с первого занятия.",
            "image_url": "",
            "features": [
                "Современные учебные материалы",
                "Интерактивные методики обучения",
                "Небольшие группы до 8 человек",
                "Индивидуальный подход к каждому студенту"
            ]
        }
    },
    # 3. BENEFITS — Преимущества
    {
        "section_type": "benefits",
        "order": 2,
        "content": {
            "title": "Почему выбирают нас",
            "items": [
                {"icon": "star", "title": "Опытные преподаватели", "description": "Сертифицированные специалисты с опытом от 5 лет"},
                {"icon": "group", "title": "Малые группы", "description": "До 8 человек для максимальной эффективности"},
                {"icon": "schedule", "title": "Гибкий график", "description": "Утренние, дневные и вечерние группы"},
                {"icon": "certificate", "title": "Сертификаты", "description": "По окончании курса выдаётся сертификат"},
                {"icon": "online", "title": "Онлайн и офлайн", "description": "Выбирайте удобный формат обучения"},
                {"icon": "support", "title": "Поддержка 24/7", "description": "Всегда на связи с учениками"}
            ]
        }
    },
    # 4. STATISTICS — Статистика/достижения
    {
        "section_type": "statistics",
        "order": 3,
        "content": {
            "title": "Наши достижения в цифрах",
            "items": [
                {"number": "5+", "label": "Лет на рынке"},
                {"number": "2000+", "label": "Выпускников"},
                {"number": "15+", "label": "Языковых курсов"},
                {"number": "98%", "label": "Довольных студентов"}
            ]
        }
    },
    # 5. COURSE_GRID — Сетка курсов (автоматически подгружает курсы компании)
    {
        "section_type": "course_grid",
        "order": 4,
        "content": {
            "title": "Наши курсы",
            "description": "Выберите подходящий курс и начните обучение",
            "show_all": True,
        }
    },
    # 6. TEACHER_SLIDER — Слайдер преподавателей (автоматически подгружает учителей компании)
    {
        "section_type": "teacher_slider",
        "order": 5,
        "content": {
            "title": "Наши преподаватели",
            "description": "Профессионалы, которые вдохновляют на изучение языков",
            "show_all": True,
        }
    },
    # 7. PRICING — Таблица цен
    {
        "section_type": "pricing",
        "order": 6,
        "content": {
            "title": "Стоимость обучения",
            "description": "Прозрачные цены без скрытых платежей",
            "items": [
                {"name": "Пробный урок", "price": "Бесплатно", "features": ["Знакомство с преподавателем", "Определение уровня", "Консультация"], "highlight": False},
                {"name": "Базовый курс", "price": "2 500 сом/мес", "features": ["2 занятия в неделю", "Разговорная практика", "Учебные материалы", "Домашние задания"], "highlight": True},
                {"name": "Интенсивный курс", "price": "4 500 сом/мес", "features": ["4 занятия в неделю", "Индивидуальный подход", "Все материалы", "Разговорный клуб", "Сертификат"], "highlight": False},
                {"name": "Индивидуально", "price": "от 800 сом/час", "features": ["Персональный график", "Программа под вас", "Максимум внимания", "Быстрый прогресс"], "highlight": False}
            ]
        }
    },
    # 8. TESTIMONIALS — Отзывы
    {
        "section_type": "testimonials",
        "order": 7,
        "content": {
            "title": "Отзывы наших студентов",
            "description": "Что говорят те, кто уже учится у нас",
            "items": [
                {"name": "Айгерим К.", "text": "Очень рада, что выбрала Turar Language Center! За 3 месяца значительно улучшила свой английский. Преподаватели настоящие профессионалы!", "rating": 5},
                {"name": "Улан М.", "text": "Гибкий график — это то, что нужно для работающих людей. Совмещаю с работой без проблем. Рекомендую!", "rating": 5},
                {"name": "Нуржан Т.", "text": "Очень уютная атмосфера, современные учебники. Заговорил на английском уже через месяц обучения. Спасибо!", "rating": 5},
                {"name": "Алия Б.", "text": "Ребёнок ходит на английский с удовольствием! Преподаватели умеют найти подход к детям. Отличный центр!", "rating": 5}
            ]
        }
    },
    # 9. VIDEO — Видео блок
    {
        "section_type": "video",
        "order": 8,
        "content": {
            "title": "Узнайте больше о нас",
            "description": "Посмотрите видео о нашем центре",
            "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "poster_url": ""
        }
    },
    # 10. GALLERY — Галерея
    {
        "section_type": "gallery",
        "order": 9,
        "content": {
            "title": "Фотогалерея",
            "description": "Как проходят наши занятия",
            "images": [
                {"url": "", "caption": "Учебный класс"},
                {"url": "", "caption": "Занятие в группе"},
                {"url": "", "caption": "Индивидуальное занятие"},
                {"url": "", "caption": "Наши студенты"},
                {"url": "", "caption": "Выпускной"},
                {"url": "", "caption": "Мероприятие"}
            ]
        }
    },
    # 11. FAQ — Часто задаваемые вопросы
    {
        "section_type": "faq",
        "order": 10,
        "content": {
            "title": "Часто задаваемые вопросы",
            "items": [
                {"question": "Нужна ли предварительная подготовка?", "answer": "Нет, мы принимаем студентов с любым уровнем подготовки. Перед началом обучения проведём бесплатное тестирование и определим ваш уровень."},
                {"question": "Как проходит пробный урок?", "answer": "Пробный урок длится 30 минут. Вы знакомитесь с преподавателем, определяете свой уровень и получаете рекомендации по программе обучения."},
                {"question": "Можно ли совмещать с работой или учёбой?", "answer": "Да, у нас гибкий график: утренние, дневные и вечерние группы. Вы можете выбрать удобное время."},
                {"question": "Выдаёте ли вы сертификаты?", "answer": "Да, после успешного завершения курса мы выдаём сертификат установленного образца."},
                {"question": "Есть ли онлайн-обучение?", "answer": "Да, мы предлагаем как офлайн, так и онлайн-формат обучения на выбор."}
            ]
        }
    },
    # 12. PARTNERS — Партнёры
    {
        "section_type": "partners",
        "order": 11,
        "content": {
            "title": "Наши партнёры",
            "description": "Компании, которые доверяют нам",
            "items": [
                {"name": "Партнёр 1", "logo_url": ""},
                {"name": "Партнёр 2", "logo_url": ""},
                {"name": "Партнёр 3", "logo_url": ""},
                {"name": "Партнёр 4", "logo_url": ""}
            ]
        }
    },
    # 13. CTA — Призыв к действию
    {
        "section_type": "cta",
        "order": 12,
        "content": {
            "title": "Готовы начать?",
            "description": "Запишитесь на бесплатный пробный урок прямо сейчас!",
            "cta_text": "Записаться",
            "cta_link": "#lead_form",
            "background_color": "#45B2EF",
        }
    },
    # 14. CONTACTS — Контакты
    {
        "section_type": "contacts",
        "order": 13,
        "content": {
            "title": "Свяжитесь с нами",
            "description": "Мы всегда рады ответить на ваши вопросы",
            "phone": company.phone or "+996 501 520 681",
            "telegram": "@turar_language",
            "whatsapp": company.phone or "+996501520681",
            "address": "г. Ош",
            "email": "info@turar.kg",
            "map_coordinates": "40.5139, 72.8163"
        }
    },
    # 15. LEAD_FORM — Форма заявки (для сбора лидов → Telegram бот)
    {
        "section_type": "lead_form",
        "order": 14,
        "content": {
            "title": "Запишитесь на бесплатный пробный урок",
            "description": "Оставьте свои контакты, и мы свяжемся с вами в ближайшее время",
            "cta_text": "Отправить заявку",
            "fields": ["full_name", "phone", "course_interest"],
            "success_message": "Спасибо! Мы свяжемся с вами в течение 15 минут."
        }
    },
]

# Создать секции
created_count = 0
for section_data in sections_data:
    section = LandingSection.objects.create(
        page=landing,
        section_type=section_data["section_type"],
        order=section_data["order"],
        content=section_data["content"]
    )
    created_count += 1
    print(f"  ✓ {section_data['order']+1}. {section_data['section_type']} — {section_data['content'].get('title', '')}")

print(f"\n✅ Всего создано секций: {created_count}")
print(f"🌐 URL лендинга: /public/landing-pages/{landing.slug}/")
print(f"📱 Полный URL: http://localhost:3001/ru/public/landing-pages/{landing.slug}/")
