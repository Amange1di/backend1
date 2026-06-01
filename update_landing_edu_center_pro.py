import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, LandingPage, LandingSection

# Найти компанию "Edu Center Pro"
company = Company.objects.filter(name="Edu Center Pro").first()
if not company:
    print("Компания 'Edu Center Pro' не найдена!")
    exit(1)

print(f"Найдена компания: {company.name} (slug: {company.slug})")

# Найти или создать лендинг
landing = LandingPage.objects.filter(company=company, status="active").first()

if not landing:
    # Найти draft лендинг
    landing = LandingPage.objects.filter(company=company, status="draft").first()
    if landing:
        landing.status = "active"
    else:
        # Создать новый
        landing = LandingPage(
            title="Edu Center Pro - Лучшее образование в Кыргызстане",
            slug=f"edu-center-pro-{company.id}",
            company=company,
            status="active",
        )
    landing.company = company
    landing.save()
    print(f"Лендинг: {landing.slug}")

# Удалить старые секции
LandingSection.objects.filter(page=landing).delete()
print("Удалены старые секции")

# Создать новые секции
sections_data = [
    {
        "type": "hero",
        "title": "Edu Center Pro",
        "subtitle": "Открываем будущее вместе!",
        "description": "Качественное образование для всех возрастов. Профессиональные курсы, дипломированные преподаватели, гибкий график обучения.",
        "cta_text": "Записаться на курс",
        "cta_link": "#courses",
        "order": 0
    },
    {
        "type": "about",
        "title": "О нас",
        "description": "Edu Center Pro - ведущий образовательный центр с опытом более 10 лет. Мы помогли тысячам студентов достичь профессиональных высот и построить успешную карьеру. Наши преподаватели - практикующие специалисты с многолетним опытом работы в ведущих компаниях страны.",
        "image_url": "/eduOshLogo.png",
        "order": 1
    },
    {
        "type": "features",
        "title": "Почему выбирают нас",
        "items": [
            {"icon": "star", "title": "Опытные преподаватели", "description": "Лучшие специалисты в своей области с многолетним опытом"},
            {"icon": "certificate", "title": "Официальные сертификаты", "description": "Документы государственного образца об окончании курсов"},
            {"icon": "group", "title": "Малые группы", "description": "До 10 человек в группе для индивидуального подхода"},
            {"icon": "schedule", "title": "Гибкий график", "description": "Учитесь в удобное время - утро, день или вечер"},
            {"icon": "location", "title": "Удобное расположение", "description": "Филиалы в центре города и в спальных районах"},
            {"icon": "support", "title": "Поддержка 24/7", "description": "Всегда на связи с нашими студентами"}
        ],
        "order": 2
    },
    {
        "type": "statistics",
        "title": "Наши достижения",
        "items": [
            {"number": "10+", "label": "Лет опыта"},
            {"number": "5000+", "label": "Выпускников"},
            {"number": "50+", "label": "Курсов"},
            {"number": "95%", "label": "Успешность"}
        ],
        "order": 3
    },
    {
        "type": "courses",
        "title": "Наши популярные курсы",
        "description": "Выберите направление, которое подходит именно вам",
        "show_all": True,
        "order": 4
    },
    {
        "type": "teachers",
        "title": "Наши преподаватели",
        "description": "Команда профессионалов с многолетним опытом",
        "show_all": True,
        "order": 5
    },
    {
        "type": "testimonials",
        "title": "Отзывы студентов",
        "description": "Что говорят наши выпускники",
        "items": [
            {
                "name": "Айнура К.",
                "text": "Отличные курсы! Преподаватели настоящие профессионалы. Получила сертификат и сразу нашла работу.",
                "rating": 5
            },
            {
                "name": "Бекжан М.",
                "text": "График обучения очень удобный. Совмещал работу и учёбу без проблем. Рекомендую!",
                "rating": 5
            },
            {
                "name": "Садыр Т.",
                "text": "Материалы актуальные, практика больше чем теория. Exactly то, что нужно для карьеры.",
                "rating": 5
            }
        ],
        "order": 6
    },
    {
        "type": "faq",
        "title": "Частые вопросы",
        "items": [
            {"question": "Нужна ли предварительная подготовка?", "answer": "Нет, у нас есть курсы для начинающих с нуля."},
            {"question": "Можно ли совмещать с работой?", "answer": "Да, у нас гибкий график - утро, день или вечер."},
            {"question": "Выдаёте ли вы сертификаты?", "answer": "Да, все выпускники получают официальные сертификаты государственного образца."},
            {"question": "Есть ли рассрочка платежа?", "answer": "Да, у нас есть рассрочка на весь курс обучения без переплат."}
        ],
        "order": 7
    },
    {
        "type": "contact",
        "title": "Свяжитесь с нами",
        "description": "Оставьте заявку и мы перезвоним в течение 15 минут",
        "phone": "+996 555 123 456",
        "email": "info@edupro.kg",
        "address": "г. Бишкек, ул. Ленина 123, офис 45",
        "telegram": "@edupro_kg",
        "whatsapp": "+996555123456",
        "order": 8
    },
    {
        "type": "lead_form",
        "title": "Записаться на консультацию",
        "description": "Оставьте свои контакты и мы свяжемся с вами",
        "cta_text": "Отправить заявку",
        "order": 9
    }
]

for section_data in sections_data:
    section_type = section_data.pop("type")
    order = section_data.pop("order")
    
    section = LandingSection.objects.create(
        page=landing,
        section_type=section_type,
        order=order,
        content=section_data
    )
    print(f"✓ Секция '{section.section_type}' создана")

print(f"\n✅ Лендинг успешно обновлён!")
print(f"URL: http://localhost:3001/ru/public/landing-pages/{landing.slug}")
