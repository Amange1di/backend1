from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
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
    color = models.CharField(max_length=7, default="#45B2EF")
    company_name = models.CharField(max_length=200, blank=True)
    max_managers = models.PositiveIntegerField(
        default=0, help_text="Maximum number of managers this course admin can create"
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

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    def get_managers_count(self) -> int:
        """Get count of managers created by this course admin"""
        if self.role != self.Role.COURSE_ADMIN:
            return 0
        return self.created_users.filter(role=self.Role.MANAGER).count()

    def can_create_manager(self) -> bool:
        """Check if this course admin can create another manager"""
        if self.role != self.Role.COURSE_ADMIN:
            return False
        return self.get_managers_count() < self.max_managers


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
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50)
    telegram = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    primary_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
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

    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="attendance"
    )
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


class TrialLead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", _("New")
        CONTACTED = "contacted", _("Contacted")
        TRIAL_SCHEDULED = "trial_scheduled", _("Trial scheduled")
        ATTENDED = "attended", _("Attended")
        NOT_ATTENDED = "not_attended", _("Not attended")
        CONVERTED = "converted", _("Converted")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Paid")
        NOT_PAID = "not_paid", _("Not paid")
        PARTIAL = "partial", _("Partial")

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    age = models.PositiveIntegerField(null=True, blank=True)
    course_interest = models.CharField(max_length=200, blank=True)
    trial_attended = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    trial_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    converted_to_student = models.BooleanField(default=False)
    group_assigned = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trial_leads",
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID
    )
    company_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In progress")
        COMPLETED = "completed", _("Completed")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")

    class RepeatType(models.TextChoices):
        NONE = "none", _("No repeat")
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
        limit_choices_to={"role": User.Role.COURSE_ADMIN},
    )
    company_name = models.CharField(max_length=200, blank=True)
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    repeat_type = models.CharField(max_length=20, choices=RepeatType.choices, default=RepeatType.NONE)
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
