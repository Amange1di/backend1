import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, UserBalance, Transaction, PromoCode

# Найдите пользователя
user = User.objects.get(username='22')
print(f"Пользователь: {user.username} ({user.role})")

# Создайте баланс
balance, created = UserBalance.objects.get_or_create(user=user)
if created:
    print(f"Создан новый баланс для {user.username}")
else:
    print(f"Баланс уже существует: {balance.balance} eC")

# Найдите промокод
try:
    promo = PromoCode.objects.get(code='12')
    print(f"Промокод найден: {promo.code}, активен: {promo.is_active}")
    
    # Проверьте, есть ли уже транзакция для этого промокода
    existing = Transaction.objects.filter(user=user, reason="Промокод: 12").first()
    if existing:
        print(f"Транзакция уже существует: {existing.amount} eC")
    else:
        # Создайте транзакцию
        Transaction.objects.create(
            user=user,
            amount=12,
            reason="Промокод: 12",
            transaction_type="deposit"
        )
        balance.balance += 12
        balance.save()
        print(f"Транзакция создана. Новый баланс: {balance.balance} eC")
except PromoCode.DoesNotExist:
    print("Промокод '12' не найден")

print(f"\nИтоговый баланс: {balance.balance} eC")