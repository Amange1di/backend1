import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import PromoCode

count = PromoCode.objects.update(is_active=False)
print(f"Все промокоды ({count} шт) теперь неактивны")
