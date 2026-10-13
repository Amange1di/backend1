"""Central registry. No cross-database foreign keys."""
from django.conf import settings
from django.db import models


class TenantCompany(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    database_alias = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CompanyMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        COURSE_ADMIN = 'course_admin', 'Course admin'
        MANAGER = 'manager', 'Manager'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(TenantCompany, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'company'], name='v2_unique_company_membership')
        ]
