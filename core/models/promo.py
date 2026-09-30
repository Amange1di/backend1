from django.db import models
from django.utils import timezone

from .accounts import User
from .finance import CompanyBalance, UserBalance


class PromoBalance(models.Model):
    """Баланс промокода — отдельный счёт для хранения монет промокода"""
    
    promo_code = models.OneToOneField(
        "PromoCode",
        on_delete=models.CASCADE,
        related_name="balance",
        help_text="Промокод"
    )
    balance = models.PositiveIntegerField(default=0, help_text="Остаток монет промокода")
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Promo Balance"
        verbose_name_plural = "Promo Balances"
    
    def __str__(self) -> str:
        return f"{self.promo_code.code} - {self.balance} eC"
    
    def add_coins(self, amount: int):
        """Добавить монеты на баланс промокода"""
        self.balance += amount
        self.save()
        PromoTransaction.objects.create(
            promo_code=self.promo_code,
            amount=amount,
            transaction_type=PromoTransaction.Type.DEPOSIT,
        )
    
    def spend_coins(self, amount: int) -> bool:
        """Списать монеты с баланса промокода. Возвращает True если успешно"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            PromoTransaction.objects.create(
                promo_code=self.promo_code,
                amount=-amount,
                transaction_type=PromoTransaction.Type.WITHDRAWAL,
            )
            return True
        return False

class PromoTransaction(models.Model):
    """История транзакций промокода"""
    
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        WITHDRAWAL = "withdrawal", "Списание (выплата)"
    
    promo_code = models.ForeignKey(
        "PromoCode",
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="Промокод"
    )
    amount = models.IntegerField(help_text="Положительное для пополнения, отрицательное для списания")
    transaction_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DEPOSIT,
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promo_transactions",
        help_text="Пользователь, получивший выплату (при WITHDRAWAL)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Promo Transaction"
        verbose_name_plural = "Promo Transactions"
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=['promo_code', '-timestamp']),
        ]
    
    def __str__(self) -> str:
        promo_str = self.promo_code.code if self.promo_code else "—"
        user_str = self.user.username if self.user else "—"
        return f"{promo_str} ({user_str}) - {self.amount} eC"

class PromoCode(models.Model):
    """Промокоды для пополнения баланса и бонусов"""
    
    class RewardType(models.TextChoices):
        COINS = "coins", "eduCoins (монеты)"
        BONUS_LIMIT = "bonus_limit", "Бонусный лимит курсов"
    
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Код промокода (например: START2026, OSH500)",
    )
    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.COINS,
    )
    reward_value = models.PositiveIntegerField(
        help_text="Количество монет или дополнительный лимит"
    )
    max_usages = models.PositiveIntegerField(
        default=100,
        help_text="Максимальное количество активаций",
    )
    current_usages = models.PositiveIntegerField(default=0)
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Дата истечения действия",
    )
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_promo_codes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"
        ordering = ("-created_at",)
    
    def __str__(self) -> str:
        return f"{self.code} - {self.reward_value} eC"
    
    def is_valid(self) -> bool:
        """Проверить действителен ли промокод"""
        if not self.is_active:
            return False
        if self.current_usages >= self.max_usages:
            return False
        if self.expiry_date and self.expiry_date < timezone.now():
            return False
        # Проверка баланса промокода
        if self.reward_type == self.RewardType.COINS:
            if hasattr(self, 'balance') and self.balance.balance < self.reward_value:
                return False
        return True
    
    def activate(self, user: User) -> bool:
        """Активировать промокод для пользователя"""
        if not self.is_valid():
            return False
        
        self.current_usages += 1
        self.save()
        
        if self.reward_type == self.RewardType.COINS:
            # Проверяем и используем баланс промокода
            if hasattr(self, 'balance') and self.balance.balance >= self.reward_value:
                self.balance.spend_coins(self.reward_value)
                
                # Если это курс-админ (компания) — зачисляем на CompanyBalance
                if user.role == User.Role.COURSE_ADMIN and user.company:
                    company_balance, created = CompanyBalance.objects.get_or_create(company=user.company)
                    company_balance.add_coins(self.reward_value, f"Промокод: {self.code}")
                else:
                    # Иначе — на личный баланс пользователя
                    user_balance, created = UserBalance.objects.get_or_create(user=user)
                    user_balance.add_coins(self.reward_value, f"Промокод: {self.code}")
            else:
                return False  # Недостаточно средств на промокоде
        elif self.reward_type == self.RewardType.BONUS_LIMIT:
            # Увеличиваем лимит курсов (реализуется в бизнес-логике)
            if user.role == User.Role.COURSE_ADMIN:
                user.max_courses = getattr(user, "max_courses", 6) + self.reward_value
                user.save()
        
        return True
