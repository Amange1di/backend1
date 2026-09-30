from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .accounts import User


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
    owner = models.ForeignKey(
        "User",
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
        "User",
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
        "LandingPage",
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
    label = models.CharField(max_length=120)
    target_page = models.ForeignKey(
        "LandingPage",
        on_delete=models.CASCADE,
        related_name="incoming_header_links",
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        company_str = self.company.name if self.company else "—"
        return f"{company_str}: {self.label} -> {self.target_page.slug}"


def build_homework_upload_path(instance, filename: str) -> str:
    company = None
    if hasattr(instance, "company") and instance.company:
        company = instance.company
    elif hasattr(instance, "task") and instance.task and instance.task.company:
        company = instance.task.company
    if not company:
        return f"homework/shared/{filename}"
    prefix = slugify(company.name) or "shared"
    return f"homework/{prefix}/{filename}"
