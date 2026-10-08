from django.db import models
from django.utils.translation import gettext_lazy as _

from .accounts import User


class TrialLead(models.Model):
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="trial_leads")

    class Status(models.TextChoices):
        NEW = "new", _("New")
        CONTACTED = "contacted", _("Contacted")
        TRIAL_SCHEDULED = "trial_scheduled", _("Trial scheduled")
        ATTENDED = "attended", _("Attended")
        NOT_ATTENDED = "not_attended", _("Not attended")
        CONVERTED = "converted", _("Converted")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Paid")
        NOT_PAID = "not_paid", _("Not paid")
        PARTIAL = "partial", _("Partial")

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    age = models.PositiveIntegerField(null=True, blank=True)
    course_interest = models.CharField(max_length=200, blank=True)
    trial_attended = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    trial_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    converted_to_student = models.BooleanField(default=False)
    group_assigned = models.ForeignKey(
        "Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trial_leads",
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID
    )
    company = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trial_leads",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.full_name

    def get_assigned_manager(self):
        """Get manager who claimed this lead, if any"""
        assignment = LeadAssignment.objects.filter(lead=self).first()
        return assignment.manager if assignment else None

class LeadAssignment(models.Model):
    """
    Tracks which manager claimed a lead via Telegram.
    First manager to click 'Взять в работу' gets assigned.
    """
    lead = models.OneToOneField(
        "TrialLead",
        on_delete=models.CASCADE,
        related_name="assignment",
    )
    manager = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_assignments",
        limit_choices_to={"role": User.Role.MANAGER},
    )
    claimed_at = models.DateTimeField(auto_now_add=True)
    telegram_message_id = models.IntegerField(null=True, blank=True, help_text="ID сообщения в Telegram")
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, help_text="Chat ID группы/канала где было отправлено")

    class Meta:
        verbose_name = "Lead Assignment"
        verbose_name_plural = "Lead Assignments"

    def __str__(self) -> str:
        return f"{self.lead.full_name} -> {self.manager}"
