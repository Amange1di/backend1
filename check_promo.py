import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import PromoCode

print("Всего промокодов:", PromoCode.objects.count())
print("\nСписок промокодов:")
for p in PromoCode.objects.all()[:20]:
    print(f"  {p.code} - {p.reward_value} ({p.reward_type}) создан: {p.created_at}")