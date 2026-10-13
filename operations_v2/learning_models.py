from django.db import models
from .models import TenantBranch, TenantGroup


class TenantLibraryItem(models.Model):
    branch = models.ForeignKey(TenantBranch, on_delete=models.PROTECT, related_name="library_items")
    title = models.CharField(max_length=200)
    resource_url = models.URLField(max_length=1000, blank=True)
    created_by_user_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TenantHomework(models.Model):
    group = models.ForeignKey(TenantGroup, on_delete=models.CASCADE, related_name="homework")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    library_item = models.ForeignKey(
        TenantLibraryItem, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="homework_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
