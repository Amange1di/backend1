import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LandingSection

s = LandingSection.objects.filter(section_type='statistics').first()
if s:
    print("Секция statistics найдена:")
    print(f"ID: {s.id}")
    print(f"Order: {s.order}")
    print(f"Content:")
    print(json.dumps(s.content, ensure_ascii=False, indent=2))
else:
    print("Секция statistics не найдена!")
