"""Compatibility facade for course-admin Telegram handlers."""

from .handlers.admin_groups import resubmit_group, resubmit_group_callback
from .handlers.admin_tasks import menu_tasks_stats, tasks_stats

__all__ = [
    "menu_tasks_stats",
    "resubmit_group",
    "resubmit_group_callback",
    "tasks_stats",
]
