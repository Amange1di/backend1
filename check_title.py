import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import LandingPage

p = LandingPage.objects.filter(slug='edu-center-pro-main').first()
if p:
    print("Old title:", repr(p.title))
    p.title = "Edu Center Pro"
    p.save()
    print("New title:", repr(p.title))
    print("✓ Title fixed!")
else:
    print("Not found!")
