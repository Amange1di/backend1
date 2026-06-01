import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company

company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    company.instagram = "@educenterpro"
    company.facebook = "educenterpro"
    company.save()
    print("✅ Instagram и Facebook сохранены!")
    print(f"  Instagram: {company.instagram}")
    print(f"  Facebook: {company.facebook}")
else:
    print("❌ Компания не найдена!")
