from pathlib import Path
from uuid import uuid4

from django.db import models
from django.utils.text import slugify

from .accounts import User


def build_library_upload_path(instance, filename: str) -> str:
    company = getattr(instance, "company", None)
    prefix = slugify(company.name) if company else "shared"
    suffix = Path(filename).suffix.lower()
    safe_name = f"{uuid4().hex}{suffix}"
    return f"library/{prefix or 'shared'}/{safe_name}"


class LibraryFolder(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="library_folders")
    course = models.ForeignKey("Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="library_folders")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    name = models.CharField(max_length=120)
    created_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="library_folders_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("company", "parent", "name")

    def __str__(self):
        return self.name


class LibraryItem(models.Model):
    class Type(models.TextChoices):
        HOMEWORK = "homework", "Homework"
        DOCUMENT = "document", "Document"
        PDF = "pdf", "PDF"
        VIDEO = "video", "Video"
        LINK = "link", "Link"
        IMAGE = "image", "Image"
        TEST = "test", "Test"

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Only me"
        COMPANY = "company", "Company"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="library_items")
    course = models.ForeignKey("Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="library_items")
    folder = models.ForeignKey("LibraryFolder", on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="library_items_created")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=30, choices=Type.choices)
    file = models.FileField(upload_to=build_library_upload_path, null=True, blank=True)
    url = models.URLField(max_length=1000, blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.COMPANY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    usage_count = models.PositiveIntegerField(default=0)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("company", "status")),
            models.Index(fields=("company", "type")),
            models.Index(fields=("company", "created_by")),
        ]

    def __str__(self):
        return self.title


class LibraryHomeworkTemplate(models.Model):
    library_item = models.OneToOneField(LibraryItem, on_delete=models.CASCADE, related_name="homework_template")
    instruction = models.TextField(blank=True)
    max_score = models.PositiveIntegerField(default=100)
    default_deadline_days = models.PositiveIntegerField(default=2)


class LibraryFavorite(models.Model):
    item = models.ForeignKey(LibraryItem, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="library_favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("item", "user")
