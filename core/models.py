from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
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

    def get_pages_count(self) -> int:
        if self.role != self.Role.COURSE_ADMIN or not self.company_name:
            return 0
        return LandingPage.objects.filter(company_name=self.company_name).count()

    def can_create_landing_page(self) -> bool:
        if self.role != self.Role.COURSE_ADMIN:
            return False
        return self.get_pages_count() < self.max_pages


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
    can_login = models.BooleanField(default=True)
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
    is_login_allowed = models.BooleanField(default=True)
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


class LandingPage(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PENDING = "pending", _("Pending")
        ACTIVE = "active", _("Active")
        REJECTED = "rejected", _("Rejected")

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=150, unique=True)
    company_name = models.CharField(max_length=200, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landing_pages",
        limit_choices_to={"role": User.Role.COURSE_ADMIN},
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    moderation_comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_landing_pages",
        limit_choices_to={"role": User.Role.ADMIN},
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at")

    def __str__(self) -> str:
        return self.title


class LandingSection(models.Model):
    class SectionType(models.TextChoices):
        HERO = "hero", _("Hero Section")
        ABOUT = "about", _("About Us")
        COURSE_GRID = "course_grid", _("Course Grid")
        TEACHER_SLIDER = "teacher_slider", _("Teacher Slider")
        STATISTICS = "statistics", _("Statistics")
        LEAD_FORM = "lead_form", _("Lead Form")
        TESTIMONIALS = "testimonials", _("Testimonials")
        FAQ = "faq", _("FAQ")
        PRICING = "pricing", _("Pricing Table")
        VIDEO = "video", _("Video Block")
        GALLERY = "gallery", _("Gallery")
        CONTACTS = "contacts", _("Contacts & Map")
        CTA = "cta", _("Call To Action")
        PARTNERS = "partners", _("Partners")
        BENEFITS = "benefits", _("Benefits")

    page = models.ForeignKey(
        LandingPage,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    section_type = models.CharField(max_length=32, choices=SectionType.choices)
    order = models.PositiveIntegerField(default=0)
    content = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return f"{self.page_id}:{self.section_type}:{self.order}"


class LandingHeaderLink(models.Model):
    company_name = models.CharField(max_length=200)
    label = models.CharField(max_length=120)
    target_page = models.ForeignKey(
        LandingPage,
        on_delete=models.CASCADE,
        related_name="incoming_header_links",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return f"{self.company_name}: {self.label} -> {self.target_page.slug}"


def build_homework_upload_path(instance, filename: str) -> str:
    company_name = ""
    if hasattr(instance, "company_name") and instance.company_name:
        company_name = instance.company_name
    elif hasattr(instance, "task") and instance.task and instance.task.company_name:
        company_name = instance.task.company_name
    prefix = slugify(company_name) or "shared"
    return f"homework/{prefix}/{filename}"


class HomeworkTask(models.Model):
    class TargetType(models.TextChoices):
        ALL_GROUP = "all_group", _("All group")
        SPECIFIC_STUDENTS = "specific_students", _("Specific students")

    class TaskType(models.TextChoices):
        HOMEWORK = "homework", _("Homework")
        QUIZ = "quiz", _("Quiz")
        PROJECT = "project", _("Project")
        EXAM = "exam", _("Exam")

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="homework_tasks",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="homework_tasks",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    company_name = models.CharField(max_length=200, blank=True)
    lesson_number = models.PositiveIntegerField(null=True, blank=True)
    is_extra_task = models.BooleanField(default=False)
    target_type = models.CharField(
        max_length=32,
        choices=TargetType.choices,
        default=TargetType.ALL_GROUP,
    )
    students = models.ManyToManyField(
        Student,
        related_name="individual_tasks",
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to=build_homework_upload_path,
        blank=True,
        null=True,
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.HOMEWORK,
    )
    deadline = models.DateTimeField()
    hard_deadline = models.BooleanField(default=False)
    allow_late = models.BooleanField(default=False)
    grace_period_minutes = models.PositiveIntegerField(default=0)
    publish_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class HomeworkTaskAttachment(models.Model):
    task = models.ForeignKey(
        HomeworkTask,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=build_homework_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Attachment #{self.pk} for {self.task_id}"


class HomeworkSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        REVIEWED = "reviewed", _("Reviewed")
        REJECTED = "rejected", _("Rejected")

    task = models.ForeignKey(
        HomeworkTask,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="homework_submissions",
    )
    answer_text = models.TextField(blank=True)
    file = models.FileField(
        upload_to=build_homework_upload_path,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    grade = models.PositiveIntegerField(null=True, blank=True)
    teacher_comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at",)
        unique_together = ("task", "student")

    def __str__(self) -> str:
        return f"{self.student} -> {self.task}"
