import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, LandingPage

# Найти компанию "Edu Center Pro"
company = Company.objects.filter(name="Edu Center Pro").first()
if not company:
    print("Компания 'Edu Center Pro' не найдена!")
    exit(1)

print(f"Найдена компания: {company.name} (slug: {company.slug})")

# Найти все лендинги компании
landings = LandingPage.objects.filter(company=company)
print(f"Найдено лендингов: {landings.count()}")

for landing in landings:
    print(f"  - {landing.slug} (статус: {landing.status})")

# Активировать первый найденный лендинг
active_landing = landings.filter(status="active").first()
if active_landing:
    print(f"\nАктивный лендинг уже существует: {active_landing.slug}")
else:
    # Активировать draft лендинг
    draft_landing = landings.filter(status="draft").first()
    if draft_landing:
        print(f"\nАктивирую лендинг: {draft_landing.slug}")
        draft_landing.status = "active"
        draft_landing.save()
        print(f"✓ Лендинг активирован: {draft_landing.slug}")
    else:
        print("\n❌ Нет лендингов для активации!")

print("\nГотово!")
print(f"URL лендинга: /public/landing-pages/{active_landing.slug if active_landing else 'НЕТ'}/")
