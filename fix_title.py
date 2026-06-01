import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LandingPage

p = LandingPage.objects.filter(slug='edu-center-pro-main').first()
if p:
    print(f"Old title: {repr(p.title)}")
    p.title = "Edu Center Pro"
    p.save()
    print(f"New title: {repr(p.title)}")
    print("✓ Title updated successfully!")
else:
    print("❌ Landing page not found!")