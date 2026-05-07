import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Transaction, User

print("=== Все транзакции ===")
for t in Transaction.objects.all():
    print(f"ID: {t.id}")
    print(f"  Пользователь: {t.user.username} ({t.user.role})")
    print(f"  Сумма: {t.amount}")
    print(f"  Причина: {t.reason}")
    print(f"  Тип: {t.get_transaction_type_display()}")
    print(f"  Время: {t.timestamp}")
    print()

print("=== Балансы пользователей ===")
from core.models import UserBalance
for b in UserBalance.objects.all():
    print(f"{b.user.username}: {b.balance} eC")
