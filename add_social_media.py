import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company

company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    # Проверяем, есть ли поля instagram и facebook
    try:
        company.instagram = "@educenterpro"
        company.facebook = "educenterpro"
        company.save()
        print("✅ Instagram и Facebook добавлены!")
        print(f"  Instagram: {company.instagram}")
        print(f"  Facebook: {company.facebook}")
    except Exception as e:
        print(f"❌ Поля instagram/facebook не существуют в модели Company: {e}")
        print("   Нужно добавить эти поля в модель Company перед сохранением.")
else:
    print("❌ Компания не найдена!")
