from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .accounts import User


class TaskLead(models.Model):
    """Task Lead - менеджер с особыми правами для управления задачами и командой"""
    
    class Role(models.TextChoices):
        TASK_LEAD = "task_lead", _("Task Lead")
        TEAM_LEAD = "team_lead", _("Team Lead")
        PROJECT_MANAGER = "project_manager", _("Project Manager")
    
    user = models.OneToOneField(
        "User",
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
        "User",
        on_delete=models.CASCADE,
        related_name="tasks",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
        limit_choices_to={"role": User.Role.COURSE_ADMIN},
    )
    task_lead = models.ForeignKey(
        "TaskLead",
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
