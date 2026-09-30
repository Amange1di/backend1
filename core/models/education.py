from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .accounts import User


class Course(models.Model):
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_weeks = models.PositiveIntegerField()
    lesson_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    schedule = models.TextField(blank=True)
    admins = models.ManyToManyField(
        "User",
        related_name="admin_courses",
        blank=True,
        limit_choices_to={"role": User.Role.COURSE_ADMIN},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_promoted = models.BooleanField(default=False, help_text="Продвигается ли курс (TOP)")
    promoted_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты продвигается")

    class Meta:
        ordering = ["-is_promoted", "-created_at"]

    def __str__(self) -> str:
        return self.title

class Auditorium(models.Model):
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=50, blank=True)
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditoriums",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        if self.name and self.number:
            return f"{self.name} {self.number}"
        return self.name or self.number or "Auditorium"

class Student(models.Model):
    user = models.OneToOneField(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50)
    telegram = models.CharField(max_length=100, blank=True)
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    can_login = models.BooleanField(default=True)
    primary_course = models.ForeignKey(
        "Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

class Group(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает подтверждения")
        ACTIVE = "active", _("Активна")
        REJECTED = "rejected", _("Отклонена")

    name = models.CharField(max_length=200)
    course = models.ForeignKey(
        "Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    teacher = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_groups",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    students = models.ManyToManyField("Student", related_name="groups", blank=True)
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    is_login_allowed = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Статус группы: active — активна, pending — ожидает подтверждения учителем",
    )
    schedule_days = models.CharField(max_length=200, blank=True)
    schedule_time = models.CharField(max_length=50, blank=True)
    auditorium = models.ForeignKey(
        "Auditorium",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    lessons_count = models.PositiveIntegerField(null=True, blank=True)
    lessons_per_month = models.PositiveIntegerField(null=True, blank=True, help_text="Количество уроков в месяц")
    total_months = models.PositiveIntegerField(null=True, blank=True, help_text="Сколько месяцев длится группа")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    rejection_comment = models.TextField(blank=True, help_text="Комментарий учителя при отказе")
    rejection_count = models.PositiveIntegerField(default=0, help_text="Количество отказов учителя")
    teacher_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Процент от оплаты, который получает учитель (0-100)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        status_icon = {
            self.Status.PENDING: "⏳",
            self.Status.ACTIVE: "✅",
            self.Status.REJECTED: "❌",
        }.get(self.status, "")
        return f"{status_icon} {self.name}"

class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", _("Present")
        ABSENT = "absent", _("Absent")
        EXCUSED = "excused", _("Excused")

    group = models.ForeignKey(
        "Group", on_delete=models.CASCADE, related_name="attendance"
    )
    student = models.ForeignKey(
        "Student", on_delete=models.CASCADE, related_name="attendance"
    )
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "student", "date")

    def __str__(self) -> str:
        return f"{self.group} - {self.student} - {self.date}"

class GroupMonth(models.Model):
    """Месяцы обучения группы с зарплатой преподавателя."""
    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает")
        COMPLETED = "completed", _("Завершён")

    group = models.ForeignKey(
        "Group",
        on_delete=models.CASCADE,
        related_name="months",
    )
    month_number = models.PositiveIntegerField(
        help_text="Номер месяца (1, 2, 3...)",
    )
    teacher_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Зарплата преподавателя за этот месяц (заполняется курс-админом)",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Когда месяц был отмечен как завершённый",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Month of group"
        verbose_name_plural = "Months of group"
        ordering = ("group", "month_number")
        unique_together = [["group", "month_number"]]

    def __str__(self) -> str:
        return f"{self.group} — месяц {self.month_number}"
