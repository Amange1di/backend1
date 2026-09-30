"""Compatibility facade for manager Telegram handlers."""

from .handlers.manager_leads import claim_lead
from .handlers.manager_tasks import menu_tasks, task_filter, task_set_status, tasks

__all__ = [
    "claim_lead",
    "menu_tasks",
    "task_filter",
    "task_set_status",
    "tasks",
]
