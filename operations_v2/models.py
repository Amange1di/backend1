"""Tenant-local operational data. Central references are scalar IDs."""
from django.db import models


class TenantBranch(models.Model):
    company_id = models.BigIntegerField(db_index=True)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company_id', 'name'], name='v2_unique_tenant_branch')
        ]


class TenantStudent(models.Model):
    central_user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    branch = models.ForeignKey(TenantBranch, on_delete=models.PROTECT, related_name='students')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)


class TenantGroup(models.Model):
    branch = models.ForeignKey(TenantBranch, on_delete=models.PROTECT, related_name='groups')
    name = models.CharField(max_length=200)
    teacher_user_id = models.BigIntegerField(null=True, blank=True)
    students = models.ManyToManyField(TenantStudent, blank=True, related_name='groups')


class TenantAttendance(models.Model):
    group = models.ForeignKey(TenantGroup, on_delete=models.CASCADE, related_name='attendance')
    student = models.ForeignKey(TenantStudent, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    present = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'student', 'date'], name='v2_unique_attendance')
        ]

# Register the schedule model with Django's app model discovery.
from .schedule_models import TenantLesson  # noqa: E402,F401

from .finance_models import TenantFinanceEntry  # noqa: E402,F401
