import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LandingPage, Company

# Находим компанию
company = Company.objects.filter(slug='edu-center-pro').first()
if not company:
    print("Компания 'edu-center-pro' не найдена!")
    exit(1)

# Находим лендинг
landing = LandingPage.objects.filter(slug='edu-center-pro-main').first()
if not landing:
    print("Лендинг 'edu-center-pro-main' не найден!")
    exit(1)

# Исправляем title
old_title = landing.title
landing.title = "Edu Center Pro - Ош"
landing.save()

print(f"✅ Title исправлен!")
print(f"   Старый: {old_title}")
print(f"   Новый: {landing.title}")
print(f"   Компания: {company.name}")