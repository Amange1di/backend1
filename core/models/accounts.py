from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", _("Super Admin")
        ADMIN = "admin", _("Admin")
        COURSE_ADMIN = "course_admin", _("Company admin")
        MANAGER = "manager", _("Manager")
        TEACHER = "teacher", _("Teacher")
        STUDENT = "student", _("Student")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TEACHER)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=255, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    salary_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    working_hours = models.CharField(max_length=255, blank=True)
    working_days = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=7, default="#45B2EF")
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_student_cabinet_enabled = models.BooleanField(default=True)
    must_set_password = models.BooleanField(default=False)
    max_managers = models.PositiveIntegerField(
        default=0, help_text="Maximum number of managers this course admin can create"
    )
    max_pages = models.PositiveIntegerField(
        default=1, help_text="Maximum number of landing pages this course admin can create"
    )
    max_blocks = models.PositiveIntegerField(
        default=7, help_text="Maximum number of sections allowed on a single landing page"
    )
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )
    teaching_courses = models.ManyToManyField(
        "Course",
        related_name="teachers",
        blank=True,
    )
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, help_text="Telegram chat ID для уведомлений")

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    def get_managers_count(self) -> int:
        """Get count of active managers created by this course admin."""
        if self.role != self.Role.COURSE_ADMIN:
            return 0
        return self.created_users.filter(
            role=self.Role.MANAGER,
            is_active=True,
        ).count()

    def can_create_manager(self) -> bool:
        """Check if this course admin can create another manager"""
        if self.role != self.Role.COURSE_ADMIN:
            return False
        return self.get_managers_count() < self.max_managers

    def get_pages_count(self) -> int:
        """Check how many landing pages this course admin has created"""
        if self.role != self.Role.COURSE_ADMIN or not self.company:
            return 0
        from .landing import LandingPage
        return LandingPage.objects.filter(company=self.company).count()

    def can_create_landing_page(self) -> bool:
        """Check if this course admin can create another landing page"""
        if self.role != self.Role.COURSE_ADMIN:
            return False
        return self.get_pages_count() < self.max_pages

class TelegramBindCode(models.Model):
    """
    Одноразовый код для первичной привязки Telegram аккаунта.
    Генерируется на сайте пользователем, вводится в боте.
    """
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="telegram_bind_codes",
    )
    code = models.CharField(max_length=6, help_text="6-значный код")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Дата истечения кода")
    is_used = models.BooleanField(default=False, help_text="Был ли код использован")

    class Meta:
        verbose_name = "Telegram Bind Code"
        verbose_name_plural = "Telegram Bind Codes"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.username}: {self.code} (used={self.is_used})"

    def is_valid(self) -> bool:
        """Код действителен если не использован и не истёк"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()


class FirstLoginCredential(models.Model):
    user = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="first_login_credential",
    )
    password_hash = models.CharField(max_length=128)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "First Login Credential"
        verbose_name_plural = "First Login Credentials"

    def __str__(self) -> str:
        return f"{self.user.username} (used={self.is_used})"
