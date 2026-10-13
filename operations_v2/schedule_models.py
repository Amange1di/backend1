from django.db import models

from .models import TenantGroup


class TenantLesson(models.Model):
    group = models.ForeignKey(TenantGroup, on_delete=models.CASCADE, related_name="lessons")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    room_name = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["starts_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="v2_lesson_ends_after_start",
            ),
        ]
