import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import PromoCode

print("Проверка всех промокодов:")
for p in PromoCode.objects.all():
    print(f"  {p.code}: is_active={p.is_active}, current_usages={p.current_usages}, max_usages={p.max_usages}, expiry={p.expiry_date}, created_by={p.created_by}")
