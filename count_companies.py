import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Company

count = Company.objects.count()
print(f"Компаний в базе: {count}")

# Показать список компаний
companies = Company.objects.all()
for c in companies:
    print(f"  - {c.name} (ID: {c.id}, slug: {c.slug})")