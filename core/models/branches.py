from django.core.exceptions import ValidationError
from django.db import models


class Branch(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    is_main = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_main", "name")
        constraints = [
            models.UniqueConstraint(fields=("company", "name"), name="uniq_branch_name_per_company"),
        ]

    def clean(self):
        if self.is_active and self.company_id:
            qs = Branch.objects.filter(company_id=self.company_id, is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.count() >= self.company.branch_limit:
                raise ValidationError({"company": "branch_limit_reached"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company} — {self.name}"
