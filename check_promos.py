import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import PromoCode

print("=== Все промокоды ===")
for p in PromoCode.objects.all():
    created_by = p.created_by.username if p.created_by else "None"
    print(f"Код: {p.code}")
    print(f"  Активен: {p.is_active}")
    print(f"  Создатель: {created_by}")
    print(f"  Награда: {p.reward_value} {p.reward_type}")
    print(f"  Использовано: {p.usage_count}/{p.max_usages}")
    print()
