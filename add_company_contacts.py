import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company

# Найти компанию
company = Company.objects.filter(slug='edu-center-pro').first()
if company:
    print(f"Обновляю контакты для: {company.name}")
    
    # Добавить контакты
    company.phone = "+996 777 123 456"
    company.telegram = "@educenterpro"
    company.whatsapp = "+996777123456"
    company.website = "https://educenter.pro"
    company.district = "Бишкек, пр. Чуй 123"
    
    company.save()
    
    print("✅ Контакты обновлены:")
    print(f"  Phone: {company.phone}")
    print(f"  Telegram: {company.telegram}")
    print(f"  WhatsApp: {company.whatsapp}")
    print(f"  Website: {company.website}")
    print(f"  District: {company.district}")
else:
    print("❌ Компания не найдена!")
