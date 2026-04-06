from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        COURSE_ADMIN = "course_admin", _("Company admin")
        TEACHER = "teacher", _("Teacher")

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.TEACHER
    )
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=255, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class Course(models.Model):
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_weeks = models.PositiveIntegerField()
    lesson_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    schedule = models.TextField(blank=True)
    admins = models.ManyToManyField(
        User,
        related_name="admin_courses",
        blank=True,
        limit_choices_to={"role": User.Role.COURSE_ADMIN},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Auditorium(models.Model):
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        if self.name and self.number:
            return f"{self.name} {self.number}"
        return self.name or self.number or "Auditorium"


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50)
    telegram = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    primary_course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Group(models.Model):
    name = models.CharField(max_length=200)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_groups",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    students = models.ManyToManyField(Student, related_name="groups", blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    schedule_days = models.CharField(max_length=200, blank=True)
    schedule_time = models.CharField(max_length=50, blank=True)
    auditorium = models.ForeignKey(
        Auditorium,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    lessons_count = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", _("Present")
        ABSENT = "absent", _("Absent")
        EXCUSED = "excused", _("Excused")

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance"
    )
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "student", "date")

    def __str__(self) -> str:
        return f"{self.group} - {self.student} - {self.date}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PAID = "paid", _("Paid")
        DEBT = "debt", _("Debt")

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="payments"
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices)
    paid_at = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.student} - {self.amount} ({self.status})"
