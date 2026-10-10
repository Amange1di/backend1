from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")

    class Status(models.TextChoices):
        PAID = "paid", _("Paid")
        DEBT = "debt", _("Debt")

    student = models.ForeignKey(
        "Student", on_delete=models.CASCADE, related_name="payments"
    )
    group = models.ForeignKey(
        "Group", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    received_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_payments",
        help_text="Сотрудник, который принял/зарегистрировал оплату",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices)
    paid_at = models.DateField(default=timezone.localdate)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Дата, до которой нужно оплатить (для напоминаний)",
    )
    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда было отправлено последнее напоминание об оплате",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.student} - {self.amount} ({self.status})"

class Expense(models.Model):
    """Расходы компании."""
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="expenses",
        help_text="Компания",
    )
    description = models.CharField(
        max_length=500,
        help_text="Описание расхода",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Сумма расхода",
    )
    category = models.CharField(
        max_length=20,
        choices=[
            ("salary", "Зарплата"),
            ("rent", "Аренда"),
            ("utilities", "Коммунальные услуги"),
            ("materials", "Учебные материалы"),
            ("marketing", "Маркетинг"),
            ("equipment", "Оборудование"),
            ("tax", "Налоги"),
            ("other", "Прочее"),
        ],
        default="other",
        help_text="Категория расхода",
    )
    date = models.DateField(
        default=timezone.localdate,
        help_text="Дата расхода",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:
        return f"{self.description} — {self.amount} ({self.date})"

class CompanyBalance(models.Model):
    """Общий баланс eduCoin для компании (course_admin и его менеджеры)"""
    
    company = models.OneToOneField(
        "Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="balance",
        help_text="Компания"
    )
    balance = models.PositiveIntegerField(default=0, help_text="Баланс eduCoins")
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Balance"
        verbose_name_plural = "Company Balances"
    
    def __str__(self) -> str:
        company_str = self.company.name if self.company else str(self.id)
        return f"{company_str} - {self.balance} eC"
    
    def add_coins(self, amount: int, reason: str, user=None):
        """Atomically add coins and write the ledger entry."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        with transaction.atomic():
            locked = (
                CompanyBalance.objects
                .select_for_update()
                .get(pk=self.pk)
            )
            locked.balance += amount
            locked.save(update_fields=["balance", "last_update"])
            Transaction.objects.create(
                company_id=locked.company_id,
                user=user,
                amount=amount,
                reason=reason,
                transaction_type=Transaction.Type.DEPOSIT,
            )
            self.balance = locked.balance
            return locked.balance

    def spend_coins(self, amount: int, reason: str) -> bool:
        """Atomically spend coins if the balance is sufficient."""
        if amount <= 0:
            return False

        with transaction.atomic():
            locked = (
                CompanyBalance.objects
                .select_for_update()
                .get(pk=self.pk)
            )
            if locked.balance < amount:
                return False

            locked.balance -= amount
            locked.save(update_fields=["balance", "last_update"])
            Transaction.objects.create(
                company_id=locked.company_id,
                amount=-amount,
                reason=reason,
                transaction_type=Transaction.Type.WITHDRAWAL,
            )
            self.balance = locked.balance
            return True

class Transaction(models.Model):
    """История транзакций eduCoin"""
    
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        WITHDRAWAL = "withdrawal", "Списание"
        BONUS = "bonus", "Бонус"
    
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Компания"
    )
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Пользователь, инициировавший транзакцию (необязательно)"
    )
    amount = models.IntegerField(help_text="Положительное для пополнения, отрицательное для списания")
    reason = models.CharField(max_length=500, help_text="Причина транзакции")
    transaction_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DEPOSIT,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=['company', '-timestamp']),
        ]
    
    def __str__(self) -> str:
        company_str = self.company.name if self.company else str(self.id)
        user_str = self.user.username if self.user else "—"
        return f"{company_str} ({user_str}) - {self.amount} eC ({self.reason})"

class UserBalance(models.Model):
    """Баланс пользователя для системы eduCoin"""
    
    user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="user_balance",
        help_text="Пользователь"
    )
    balance = models.PositiveIntegerField(default=0, help_text="Баланс eduCoins")
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Balance"
        verbose_name_plural = "User Balances"
    
    def __str__(self) -> str:
        return f"{self.user.username} - {self.balance} eC"
    
    def add_coins(self, amount: int, reason: str):
        """Atomically add coins and write the user ledger entry."""
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        with transaction.atomic():
            locked = (
                UserBalance.objects
                .select_for_update()
                .get(pk=self.pk)
            )
            locked.balance += amount
            locked.save(update_fields=["balance", "last_update"])
            UserTransaction.objects.create(
                user_id=locked.user_id,
                amount=amount,
                reason=reason,
                transaction_type=UserTransaction.Type.DEPOSIT,
            )
            self.balance = locked.balance
            return locked.balance

    def spend_coins(self, amount: int, reason: str) -> bool:
        """Atomically spend user coins if the balance is sufficient."""
        if amount <= 0:
            return False

        with transaction.atomic():
            locked = (
                UserBalance.objects
                .select_for_update()
                .get(pk=self.pk)
            )
            if locked.balance < amount:
                return False

            locked.balance -= amount
            locked.save(update_fields=["balance", "last_update"])
            UserTransaction.objects.create(
                user_id=locked.user_id,
                amount=-amount,
                reason=reason,
                transaction_type=UserTransaction.Type.WITHDRAWAL,
            )
            self.balance = locked.balance
            return True

class UserTransaction(models.Model):
    """История транзакций пользователя eduCoin"""
    
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        WITHDRAWAL = "withdrawal", "Списание"
        BONUS = "bonus", "Бонус"
    
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="user_transactions",
        help_text="Пользователь"
    )
    amount = models.IntegerField(help_text="Положительное для пополнения, отрицательное для списания")
    reason = models.CharField(max_length=500, help_text="Причина транзакции")
    transaction_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DEPOSIT,
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Transaction"
        verbose_name_plural = "User Transactions"
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self) -> str:
        user_str = self.user.username if self.user else "—"
        return f"{user_str} - {self.amount} eC ({self.reason})"
