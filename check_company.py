import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, LandingPage

# Найти компанию
company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    print(f"Компания: {company.name}")
    print(f"  ID: {company.id}")
    print(f"  Phone: {company.phone}")
    print(f"  Telegram: {company.telegram}")
    print(f"  WhatsApp: {company.whatsapp}")
    print(f"  Website: {company.website}")
    print(f"  City: {company.city}")
    print(f"  District: {company.district}")
    print()
    
    # Найти лендинг
    landing = LandingPage.objects.filter(company=company, slug='edu-center-pro-main').first()
    if landing:
        print(f"Лендинг: {landing.title}")
        print(f"  Slug: {landing.slug}")
        print(f"  Status: {landing.status}")
        print(f"  Sections: {landing.sections.count()}")
    else:
        print("Лендинг не найден!")
else:
    print("Компания не найдена!")
