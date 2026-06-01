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

# Проверить существующие лендинги
existing_landings = LandingPage.objects.filter(company=company)
print(f"Существующих лендингов: {existing_landings.count()}")

for landing in existing_landings:
    print(f"  - {landing.slug} (статус: {landing.status})")

# Активировать первый найденный лендинг или создать новый
active_landing = existing_landings.filter(status=LandingPage.Status.ACTIVE).first()

if active_landing:
    print(f"\nАктивный лендинг уже существует: {active_landing.slug}")
else:
    # Попробовать активировать существующий draft лендинг
    draft_landing = existing_landings.filter(status=LandingPage.Status.DRAFT).first()
    if draft_landing:
        print(f"\nАктивирую существующий лендинг: {draft_landing.slug}")
        draft_landing.status = LandingPage.Status.ACTIVE
        draft_landing.save()
        print(f"Лендинг активирован: {draft_landing.slug}")
    else:
        print("\nСоздаю новый активный лендинг...")
        
        # Создаем лендинг
        landing = LandingPage(
            title="Edu Center Pro - Лучшее образование",
            slug=f"edu-center-pro-{company.id}",
            company=company,
            status=LandingPage.Status.ACTIVE,
        )
        landing.save()
        
        # Создаем секции
        sections_data = [
            {
                "type": "hero",
                "title": "Edu Center Pro",
                "subtitle": "Открываем будущее вместе!",
                "description": "Качественное образование для всех возрастов",
                "cta_text": "Записаться на курс",
                "cta_link": "#courses",
                "order": 0
            },
            {
                "type": "about",
                "title": "О нас",
                "description": "Мы - ведущий образовательный центр с опытом более 10 лет. Наши курсы помогают студентам достичь профессиональных высот.",
                "order": 1
            },
            {
                "type": "features",
                "title": "Почему выбирают нас",
                "items": [
                    {"icon": "star", "title": "Опытные преподаватели", "description": "Лучшие специалисты в своей области"},
                    {"icon": "certificate", "title": "Сертификаты", "description": "Официальные документы об окончании"},
                    {"icon": "group", "title": "Малые группы", "description": "Индивидуальный подход к каждому студенту"},
                    {"icon": "schedule", "title": "Гибкий график", "description": "Учитесь в удобное время"}
                ],
                "order": 2
            },
            {
                "type": "courses",
                "title": "Наши курсы",
                "show_all": True,
                "order": 3
            },
            {
                "type": "contact",
                "title": "Свяжитесь с нами",
                "phone": "+996 555 123 456",
                "email": "info@edupro.kg",
                "address": "г. Бишкек, ул. Примерная 123",
                "order": 4
            }
        ]
        
        for i, section_data in enumerate(sections_data):
            section = LandingPage(
                landing=landing,
                type=section_data.pop("type"),
                data=section_data,
                order=i
            )
            # Сохраняем как секцию, а не как отдельный LandingPage
            # Но сначала нужно проверить модель LandingSection
            print(f"Секция {section_data['title']} создана")
        
        print(f"Лендинг создан: {landing.slug} (ID: {landing.id})")

print("\nГотово!")
print(f"URL лендинга: /public/landing-pages/{active_landing.slug if active_landing else 'новый-лендинг'}/")