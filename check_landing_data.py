import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LandingPage

landing = LandingPage.objects.filter(slug="edu-center-pro-main").first()
if not landing:
    print("Лендинг не найден!")
    exit(1)

print(f"Лендинг: {landing.title}")
print(f"Статус: {landing.status}")
print(f"Компания: {landing.company.name if landing.company else 'None'}")
print(f"\nСекции ({landing.sections.count()}):")

for section in landing.sections.all():
    print(f"\n  [{section.order}] {section.section_type}")
    print(f"      content: {json.dumps(section.content, ensure_ascii=False, indent=2)}")
