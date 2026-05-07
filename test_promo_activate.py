import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import PromoCode, User, UserBalance, Transaction
from django.utils import timezone
from datetime import timedelta
import random

# Создаем или получаем тестовый промокод с уникальным кодом
unique_code = f"TEST{random.randint(10000, 99999)}"
promo_code, created = PromoCode.objects.get_or_create(
    code=unique_code,
    defaults={
        "reward_type": PromoCode.RewardType.COINS,
        "reward_value": 500,
        "max_usages": 100,
        "current_usages": 0,
        "expiry_date": timezone.now() + timedelta(days=30),
        "is_active": True,
        "created_by": User.objects.filter(role=User.Role.ADMIN).first()
    }
)

if created:
    print(f"Создан новый промокод: {promo_code.code}")
else:
    print(f"Используем существующий промокод: {promo_code.code}")

print(f"  reward_value: {promo_code.reward_value}")
print(f"  is_active: {promo_code.is_active}")
print(f"  expiry_date: {promo_code.expiry_date}")
print(f"  current_usages: {promo_code.current_usages}")

# Получаем первого менеджера или course_admin
user = User.objects.filter(role__in=[User.Role.MANAGER, User.Role.COURSE_ADMIN]).first()
if user:
    print(f"\nТестируем активацию для пользователя: {user.username} ({user.role})")
    
    # Проверяем is_valid()
    print(f"  is_valid(): {promo_code.is_valid()}")
    
    # Получаем текущий баланс
    initial_balance = user.balance.balance if hasattr(user, 'balance') else 0
    print(f"  Начальный баланс: {initial_balance}")
    
    # Пробуем активировать через метод модели
    result = promo_code.activate(user)
    print(f"  activate() результат: {result}")
    
    # Проверяем баланс
    if hasattr(user, 'balance'):
        print(f"  Конечный баланс: {user.balance.balance}")
        print(f"  Начислено: {user.balance.balance - initial_balance}")
    
    # Проверяем транзакции
    transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:5]
    print(f"  Последние транзакции:")
    for t in transactions:
        print(f"    {t.amount} eC - {t.reason}")
    
    # Обновляем промокод
    promo_code.refresh_from_db()
    print(f"  current_usages после активации: {promo_code.current_usages}")
else:
    print("Нет пользователей с ролью MANAGER или COURSE_ADMIN")
