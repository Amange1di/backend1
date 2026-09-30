from django.db import models
from django.utils.translation import gettext_lazy as _

from .accounts import User


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
        "Group",
        on_delete=models.CASCADE,
        related_name="homework_tasks",
    )
    teacher = models.ForeignKey(
        "User",
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
    lesson_number = models.PositiveIntegerField(null=True, blank=True)
    is_extra_task = models.BooleanField(default=False)
    target_type = models.CharField(
        max_length=32,
        choices=TargetType.choices,
        default=TargetType.ALL_GROUP,
    )
    students = models.ManyToManyField(
        "Student",
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
        "HomeworkTask",
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
        "HomeworkTask",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        "Student",
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
