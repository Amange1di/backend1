"""Small, read-only helpers used by the production data migration commands."""

from __future__ import annotations

from django.apps import apps


# These names are deliberately stable operational categories, not a complete
# database dump.  They are the minimum records that must be compared before
# and after moving an existing EduOsh database.
INVENTORY_MODELS = {
    "users": ("core", "User", None),
    "companies": ("core", "Company", None),
    "students": ("core", "Student", None),
    "teachers": ("core", "User", {"role": "teacher"}),
    "courses": ("core", "Course", None),
    "groups": ("core", "Group", None),
    "attendance": ("core", "Attendance", None),
    "homework_tasks": ("core", "HomeworkTask", None),
    "homework_submissions": ("core", "HomeworkSubmission", None),
    "payments": ("core", "Payment", None),
    "transactions": ("core", "Transaction", None),
    "contracts": ("core", "Contract", None),
    "trial_leads": ("core", "TrialLead", None),
}


def critical_counts() -> dict[str, int]:
    """Return the minimum data-preservation inventory without changing data."""
    return {
        name: apps.get_model(app_label, model_name).objects.filter(**(filters or {})).count()
        for name, (app_label, model_name, filters) in INVENTORY_MODELS.items()
    }


def existing_application_records() -> dict[str, int]:
    """Return all non-empty project tables that make fixture import unsafe."""
    records: dict[str, int] = {}
    for app_label in ("core", "finance", "authtoken"):
        for model in apps.get_app_config(app_label).get_models():
            if model._meta.auto_created:
                continue
            count = model._default_manager.count()
            if count:
                records[model._meta.label] = count
    return records
