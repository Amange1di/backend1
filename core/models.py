from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
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
    color = models.CharField(max_length=7, default="#45B2EF")
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    # Устаревшее поле для миграции
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
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, help_text="Telegram chat ID для уведомлений")

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
        """Check how many landing pages this course admin has created"""
        if self.role != self.Role.COURSE_ADMIN or not self.company:
            return 0
        from .models import LandingPage
        return LandingPage.objects.filter(company=self.company).count()


class TelegramBindCode(models.Model):
    """
    Одноразовый код для первичной привязки Telegram аккаунта.
    Генерируется на сайте пользователем, вводится в боте.
    """
    user = models.ForeignKey(
        User,
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
    # Устаревшее поле для миграции
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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    # Устаревшее поле для миграции
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
    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает подтверждения")
        ACTIVE = "active", _("Активна")
        REJECTED = "rejected", _("Отклонена")

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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(max_length=200, blank=True)
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
        Auditorium,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groups",
    )
    lessons_count = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    rejection_comment = models.TextField(blank=True, help_text="Комментарий учителя при отказе")
    rejection_count = models.PositiveIntegerField(default=0, help_text="Количество отказов учителя")
    created_at = models.DateTimeField(auto_now_add=True)

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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trial_leads",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name

    def get_assigned_manager(self):
        """Get manager who claimed this lead, if any"""
        assignment = LeadAssignment.objects.filter(lead=self).first()
        return assignment.manager if assignment else None


class LeadAssignment(models.Model):
    """
    Tracks which manager claimed a lead via Telegram.
    First manager to click 'Взять в работу' gets assigned.
    """
    lead = models.OneToOneField(
        TrialLead,
        on_delete=models.CASCADE,
        related_name="assignment",
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_assignments",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    claimed_at = models.DateTimeField(auto_now_add=True)
    telegram_message_id = models.IntegerField(null=True, blank=True, help_text="ID сообщения в Telegram")
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, help_text="Chat ID группы/канала где было отправлено")

    class Meta:
        verbose_name = "Lead Assignment"
        verbose_name_plural = "Lead Assignments"

    def __str__(self) -> str:
        return f"{self.lead.full_name} -> {self.manager}"


class TaskLead(models.Model):
    """Task Lead - менеджер с особыми правами для управления задачами и командой"""
    
    class Role(models.TextChoices):
        TASK_LEAD = "task_lead", _("Task Lead")
        TEAM_LEAD = "team_lead", _("Team Lead")
        PROJECT_MANAGER = "project_manager", _("Project Manager")
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="task_lead_profile",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.TASK_LEAD,
        verbose_name="Роль в команде"
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="task_leads",
        verbose_name="Компания"
    )
    team_size = models.PositiveIntegerField(
        default=0,
        verbose_name="Размер команды",
        help_text="Количество подчинённых менеджеров"
    )
    max_tasks = models.PositiveIntegerField(
        default=50,
        verbose_name="Максимальное количество задач",
        help_text="Максимальное количество активных задач"
    )
    performance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Оценка эффективности",
        help_text="От 0 до 100"
    )
    responsibilities = models.TextField(
        blank=True,
        verbose_name="Обязанности",
        help_text="Описание основных обязанностей"
    )
    target_metrics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Целевые показатели",
        help_text="Ключевые показатели эффективности (KPI)"
    )
    start_date = models.DateField(
        default=timezone.localdate,
        verbose_name="Дата начала работы"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Task Lead"
        verbose_name_plural = "Task Leads"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def get_active_tasks_count(self) -> int:
        """Получить количество активных задач"""
        return Task.objects.filter(
            assigned_to__task_lead_profile__isnull=False,
            company=self.company,
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        ).count()
    
    def can_create_task(self) -> bool:
        """Проверить можно ли создавать новые задачи"""
        return self.get_active_tasks_count() < self.max_tasks


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
    task_lead = models.ForeignKey(
        TaskLead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Task Lead, ответственный за задачу"
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(max_length=200, blank=True)
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    repeat_type = models.CharField(max_length=20, choices=RepeatType.choices, default=RepeatType.NONE)
    is_seen = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "due_date"]

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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="landing_pages",
    )
    # Устаревшее поле для миграции
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
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="header_links",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(max_length=200, blank=True)
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
        return f"{self.company_name or self.company_id}: {self.label} -> {self.target_page.slug}"


def build_homework_upload_path(instance, filename: str) -> str:
    company = None
    if hasattr(instance, "company") and instance.company:
        company = instance.company
    elif hasattr(instance, "task") and instance.task and instance.task.company:
        company = instance.task.company
    if not company:
        company_name = ""
        if hasattr(instance, "company_name") and instance.company_name:
            company_name = instance.company_name
        elif hasattr(instance, "task") and instance.task and instance.task.company_name:
            company_name = instance.task.company_name
        prefix = slugify(company_name) or "shared"
        return f"homework/{prefix}/{filename}"
    prefix = slugify(company.name) or "shared"
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
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homework_tasks",
    )
    # Устаревшее поле для миграции
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


# Marketplace Application Models
class ApplicationStatus(models.TextChoices):
    NEW = "new", _("New")
    PROCESSING = "processing", _("In Processing")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


class ApplicationType(models.TextChoices):
    TEACHER = "teacher", _("Teacher")
    STUDENT = "student", _("Student")


class TeacherApplication(models.Model):
    """Model for teacher applications to join companies"""

    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    phone = models.CharField(max_length=50, verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email")
    experience = models.PositiveIntegerField(
        default=0, verbose_name="Years of Experience"
    )
    specialization = models.CharField(
        max_length=500, blank=True, verbose_name="Specialization"
    )
    expected_salary = models.CharField(
        max_length=100, blank=True, verbose_name="Expected Salary"
    )
    education = models.TextField(blank=True, verbose_name="Education")
    about = models.TextField(blank=True, verbose_name="About Me")
    availability = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Available Time Slots",
        help_text="Dictionary with keys like 'mon-morning', 'tue-afternoon', etc.",
    )
    format = models.CharField(
        max_length=20,
        choices=[("online", "Online"), ("offline", "Offline"), ("both", "Both")],
        default="online",
        verbose_name="Teaching Format",
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_applications",
        verbose_name="Company",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(
        max_length=200, blank=True, verbose_name="Company Name"
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Teacher Application"
        verbose_name_plural = "Teacher Applications"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} - {self.get_status_display()}"


class StudentApplication(models.Model):
    """Model for student applications to enroll in courses"""

    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    phone = models.CharField(max_length=50, verbose_name="Phone Number")
    email = models.EmailField(verbose_name="Email", blank=True)
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Age")
    course_interest = models.CharField(
        max_length=200, blank=True, verbose_name="Course of Interest"
    )
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ("beginner", "Beginner"),
            ("elementary", "Elementary"),
            ("intermediate", "Intermediate"),
            ("upper-intermediate", "Upper-Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
        verbose_name="Experience Level",
    )
    learning_goal = models.CharField(
        max_length=300, blank=True, verbose_name="Learning Goal"
    )
    budget = models.CharField(max_length=100, blank=True, verbose_name="Budget")
    schedule_preference = models.CharField(
        max_length=100, blank=True, verbose_name="Schedule Preference"
    )
    source = models.CharField(
        max_length=200, blank=True, verbose_name="How Did You Find Us?"
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_applications",
        verbose_name="Company",
    )
    # Устаревшее поле для миграции
    company_name = models.CharField(
        max_length=200, blank=True, verbose_name="Company Name"
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Application"
        verbose_name_plural = "Student Applications"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} - {self.get_status_display()}"


# Marketplace Public Models

class CompanyCategory(models.TextChoices):
    LANGUAGES = "languages", "Languages"
    IT = "it", "IT & Technology"
    CRAFTS = "crafts", "Crafts & Handmade"
    SPORTS = "sports", "Sports & Fitness"
    MUSIC = "music", "Music & Arts"
    BUSINESS = "business", "Business & Finance"
    OTHER = "other", "Other"


class CompanyCity(models.TextChoices):
    BISHKEK = "Бишкек", "Бишкек"
    OSH = "Ош", "Ош"
    TALAS = "Талас", "Талас"
    NARYN = "Нарын", "Нарын"
    JALAL_ABAD = "Джалал-Абад", "Джалал-Абад"
    KARAKOL = "Каракол", "Каракол"
    ONLINE = "Онлайн", "Онлайн"


class Company(models.Model):
    """Public company profile for marketplace"""
    
    name = models.CharField(max_length=200, verbose_name="Company Name")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Slug")
    logo = models.ImageField(
        upload_to="companies/logos/",
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="District"
    )
    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    whatsapp = models.CharField(max_length=100, blank=True, verbose_name="WhatsApp")
    website = models.URLField(blank=True, verbose_name="Website")
    instagram = models.CharField(max_length=100, blank=True, verbose_name="Instagram")
    facebook = models.CharField(max_length=100, blank=True, verbose_name="Facebook")
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name="Rating"
    )
    reviews_count = models.PositiveIntegerField(default=0, verbose_name="Reviews Count")
    
    # Admin user who owns this company
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="companies",
        limit_choices_to={"role": User.Role.COURSE_ADMIN}
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class JobVacancy(models.Model):
    """Job vacancy posted by companies"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="vacancies"
    )
    title = models.CharField(max_length=200, verbose_name="Position Title")
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="District"
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True, verbose_name="Min Salary")
    salary_max = models.PositiveIntegerField(null=True, blank=True, verbose_name="Max Salary")
    schedule = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Work Schedule"
    )
    requirements = models.TextField(blank=True, verbose_name="Requirements")
    responsibilities = models.TextField(blank=True, verbose_name="Responsibilities")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_promoted = models.BooleanField(default=False, help_text="Продвигается ли вакансия (TOP)")
    promoted_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты продвигается")
    is_urgent = models.BooleanField(default=False, help_text="Срочный бейдж")
    urgent_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты бейдж")
    views = models.PositiveIntegerField(default=0, verbose_name="Views")
    applications = models.PositiveIntegerField(default=0, verbose_name="Applications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Job Vacancy"
        verbose_name_plural = "Job Vacancies"
        ordering = ["-is_promoted", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name}"


class PublicCourse(models.Model):
    """Public course offered by companies"""
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    title = models.CharField(max_length=200, verbose_name="Course Title")
    slug = models.SlugField(max_length=150, verbose_name="Slug")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price"
    )
    duration_weeks = models.PositiveIntegerField(verbose_name="Duration (weeks)")
    lesson_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Lesson Duration (minutes)"
    )
    description = models.TextField(verbose_name="Description")
    category = models.CharField(
        max_length=20,
        choices=CompanyCategory.choices,
        verbose_name="Category"
    )
    city = models.CharField(
        max_length=20,
        choices=CompanyCity.choices,
        verbose_name="City"
    )
    schedule = models.TextField(blank=True, verbose_name="Schedule")
    requirements = models.TextField(blank=True, verbose_name="Requirements")
    
    # Course materials
    curriculum = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Curriculum",
        help_text="List of lessons/modules"
    )
    
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name="Rating"
    )
    reviews_count = models.PositiveIntegerField(default=0, verbose_name="Reviews Count")
    
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_promoted = models.BooleanField(default=False, help_text="Продвигается ли курс (TOP)")
    promoted_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты продвигается")
    is_urgent = models.BooleanField(default=False, help_text="Срочный бейдж")
    urgent_until = models.DateTimeField(null=True, blank=True, help_text="До какой даты бейдж")
    image = models.ImageField(
        upload_to="courses/images/",
        blank=True,
        null=True,
        verbose_name="Course Image"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Views")
    applications_count = models.PositiveIntegerField(default=0, verbose_name="Applications Count")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Public Course"
        verbose_name_plural = "Public Courses"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while PublicCourse.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class CourseApplication(models.Model):
    """Application for a course by students"""
    
    course = models.ForeignKey(
        PublicCourse,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    phone = models.CharField(max_length=50, verbose_name="Phone")
    email = models.EmailField(blank=True, verbose_name="Email")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="Age")
    experience_level = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Experience Level"
    )
    learning_goal = models.TextField(blank=True, verbose_name="Learning Goal")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course Application"
        verbose_name_plural = "Course Applications"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.full_name} - {self.course.title}"


# === Marketplace Monetization Models ===

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
    # Устаревшее поле для миграции
    company_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Название компании (устаревшее)"
    )
    balance = models.PositiveIntegerField(default=0, help_text="Баланс eduCoins")
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Company Balance"
        verbose_name_plural = "Company Balances"
    
    def __str__(self) -> str:
        company_str = self.company.name if self.company else self.company_name
        return f"{company_str} - {self.balance} eC"
    
    def add_coins(self, amount: int, reason: str):
        """Добавить монеты"""
        self.balance += amount
        self.save()
        Transaction.objects.create(
            company=self.company,
            company_name=self.company_name,
            amount=amount,
            reason=reason,
            transaction_type=Transaction.Type.DEPOSIT,
        )
    
    def spend_coins(self, amount: int, reason: str) -> bool:
        """Списать монеты. Возвращает True если успешно"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            Transaction.objects.create(
                company=self.company,
                company_name=self.company_name,
                amount=-amount,
                reason=reason,
                transaction_type=Transaction.Type.WITHDRAWAL,
            )
            return True
        return False


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
    # Устаревшее поле для миграции
    company_name = models.CharField(
        max_length=200,
        help_text="Название компании (устаревшее)"
    )
    user = models.ForeignKey(
        User,
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
            models.Index(fields=['company_name', '-timestamp']),
        ]
    
    def __str__(self) -> str:
        company_str = self.company.name if self.company else self.company_name
        user_str = self.user.username if self.user else "—"
        return f"{company_str} ({user_str}) - {self.amount} eC ({self.reason})"


class UserBalance(models.Model):
    """Баланс пользователя для системы eduCoin"""
    
    user = models.OneToOneField(
        User,
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
        """Добавить монеты"""
        self.balance += amount
        self.save()
        UserTransaction.objects.create(
            user=self.user,
            amount=amount,
            reason=reason,
            transaction_type=UserTransaction.Type.DEPOSIT,
        )
    
    def spend_coins(self, amount: int, reason: str) -> bool:
        """Списать монеты. Возвращает True если успешно"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            UserTransaction.objects.create(
                user=self.user,
                amount=-amount,
                reason=reason,
                transaction_type=UserTransaction.Type.WITHDRAWAL,
            )
            return True
        return False


class UserTransaction(models.Model):
    """История транзакций пользователя eduCoin"""
    
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Пополнение"
        WITHDRAWAL = "withdrawal", "Списание"
        BONUS = "bonus", "Бонус"
    
    user = models.ForeignKey(
        User,
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
        User,
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
        User,
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
