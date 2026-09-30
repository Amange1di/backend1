"""Compatibility facade for teacher Telegram handlers."""

from .handlers.teacher_groups import (
    cancel_action,
    confirm_group,
    confirm_group_yes,
    handle_rejection_comment,
    reject_group,
    reject_group_yes,
)
from .handlers.teacher_schedule import menu_schedule, schedule
from .handlers.teacher_students import (
    handle_students_back,
    menu_students,
    show_group_students,
    students,
)

__all__ = [
    "cancel_action",
    "confirm_group",
    "confirm_group_yes",
    "handle_rejection_comment",
    "handle_students_back",
    "menu_schedule",
    "menu_students",
    "reject_group",
    "reject_group_yes",
    "schedule",
    "show_group_students",
    "students",
]
