from django.db import models
from django.utils.translation import gettext_lazy as _


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


class PlatformApplication(models.Model):
    """Application from an education center that wants to use EduOsh."""

    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    center_name = models.CharField(max_length=200, verbose_name="Education Center")
    phone = models.CharField(max_length=50, verbose_name="Phone Number")
    comment = models.TextField(blank=True, verbose_name="Comment")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.NEW,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Application"
        verbose_name_plural = "Platform Applications"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.center_name} — {self.full_name}"
