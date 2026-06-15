"""
Async ORM helpers and utility functions.

All database access goes through ``@sync_to_async`` wrappers defined here.
"""

from datetime import timedelta
from typing import Optional

from core.models import (
    User,
    TrialLead,
    LeadAssignment,
    Group,
    HomeworkSubmission,
    HomeworkTask,
    Student,
    Task,
    TelegramBindCode,
)

from .config import (
    sync_to_async,
    Q,
    timezone,
    logger,
)


# ═══════════════════════════════════════════════════════════════════════
#  USER HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_user_by_username(username: str):
    return User.objects.get(username=username)


@sync_to_async
def _get_user_by_chat_id(chat_id: int):
    return User.objects.filter(telegram_chat_id=chat_id).first()


@sync_to_async
def _save_telegram_chat_id(user: User, chat_id: int):
    # Clear this chat_id from any other users to avoid duplicate bindings
    User.objects.filter(telegram_chat_id=chat_id).exclude(id=user.id).update(
        telegram_chat_id=None
    )
    user.telegram_chat_id = chat_id
    user.save(update_fields=["telegram_chat_id"])


@sync_to_async
def _get_managers_for_company(company_name: str):
    return list(
        User.objects.filter(
            role=User.Role.MANAGER,
            company_name=company_name,
            telegram_chat_id__isnull=False,
        ).exclude(telegram_chat_id=0)
    )


@sync_to_async
def _get_teachers_for_company(company_name: str):
    return list(
        User.objects.filter(
            role=User.Role.TEACHER,
            company_name=company_name,
            telegram_chat_id__isnull=False,
        ).exclude(telegram_chat_id=0)
    )


@sync_to_async
def _get_course_admins_for_company(company_name: str):
    return list(
        User.objects.filter(
            role=User.Role.COURSE_ADMIN,
            company_name=company_name,
            telegram_chat_id__isnull=False,
        ).exclude(telegram_chat_id=0)
    )


@sync_to_async
def _get_superadmins():
    return list(
        User.objects.filter(
            role=User.Role.SUPER_ADMIN,
            telegram_chat_id__isnull=False,
        ).exclude(telegram_chat_id=0)
    )


@sync_to_async
def _get_teachers_with_chat_id():
    return list(
        User.objects.filter(
            role=User.Role.TEACHER,
            telegram_chat_id__isnull=False,
        ).exclude(telegram_chat_id=0)
    )


# ═══════════════════════════════════════════════════════════════════════
#  GROUP HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_group_by_id(group_id: int):
    return Group.objects.select_related("course", "teacher").get(id=group_id)


@sync_to_async
def _get_teacher_groups(teacher: User):
    """Get all active and pending groups for a teacher, ordered by course name."""
    return list(
        Group.objects.filter(
            teacher=teacher,
            status__in=[Group.Status.ACTIVE, Group.Status.PENDING],
        ).select_related("course", "auditorium").order_by("course__title", "name")
    )


@sync_to_async
def _get_teacher_groups_by_name(teacher: User, query: str):
    """Find active groups for a teacher matching name or ID."""
    q = query.strip()
    if q.isdigit():
        group = Group.objects.filter(
            id=int(q),
            teacher=teacher,
            status=Group.Status.ACTIVE,
        ).select_related("course", "auditorium").first()
        if group:
            return [group]
    return list(
        Group.objects.filter(
            teacher=teacher,
            status=Group.Status.ACTIVE,
            name__icontains=q,
        ).select_related("course", "auditorium").order_by("course__title", "name")
    )


@sync_to_async
def _update_group_status(group_id: int, status: str):
    Group.objects.filter(id=group_id).update(status=status)


@sync_to_async
def _get_today_groups_for_teacher(teacher: User):
    """Get active and pending groups for a teacher that have lessons today."""
    today = timezone.localdate()
    weekday = today.weekday()
    weekday_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    weekday_name = weekday_names[weekday]
    return list(
        Group.objects.filter(
            teacher=teacher,
            status__in=[Group.Status.ACTIVE, Group.Status.PENDING],
            schedule_days__icontains=weekday_name,
            start_date__lte=today,
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).select_related("course", "auditorium").order_by("course__title", "name")
    )


@sync_to_async
def _get_week_groups_for_teacher(teacher: User):
    """Get active groups for a teacher for the current week (Mon-Sun), grouped by day."""
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    groups = list(
        Group.objects.filter(
            teacher=teacher,
            status=Group.Status.ACTIVE,
            schedule_days__isnull=False,
            schedule_time__isnull=False,
            start_date__lte=sunday,
        ).filter(
            Q(end_date__gte=monday) | Q(end_date__isnull=True)
        ).select_related("course", "auditorium").order_by("schedule_time")
    )

    weekday_names_ru = [
        "Понедельник", "Вторник", "Среда",
        "Четверг", "Пятница", "Суббота", "Воскресенье",
    ]

    result: dict[int, list[Group]] = {i: [] for i in range(7)}
    for group in groups:
        days = parse_schedule_days(group.schedule_days)
        for day_idx in days:
            lesson_date = monday + timedelta(days=day_idx)
            if lesson_date < (group.start_date or monday):
                continue
            if group.end_date and lesson_date > group.end_date:
                continue
            result[day_idx].append(group)

    return result, weekday_names_ru, today, monday


@sync_to_async
def _get_group_course_name(group) -> str:
    return group.course.title if group.course else "—"


@sync_to_async
def _get_group_company_name(group) -> Optional[str]:
    return group.company_name or (group.company.name if group.company else None)


# ═══════════════════════════════════════════════════════════════════════
#  STUDENT HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_students_for_group(group_id: int):
    """Get students in a group who have telegram_chat_id."""
    return list(
        Student.objects.filter(
            groups__id=group_id,
            user__telegram_chat_id__isnull=False,
        ).exclude(user__telegram_chat_id=0).select_related("user")
    )


@sync_to_async
def _get_all_students_for_group(group_id: int):
    """Get all students (not just those with telegram) in a group."""
    return list(
        Student.objects.filter(
            groups__id=group_id,
        ).order_by("first_name", "last_name")
    )


@sync_to_async
def _get_student_name(student) -> str:
    return f"{student.first_name} {student.last_name}".strip() or str(student.id)


# ═══════════════════════════════════════════════════════════════════════
#  LEAD HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_lead_by_id(lead_id: int):
    return TrialLead.objects.get(id=lead_id)


@sync_to_async
def _get_lead_assignment(lead: TrialLead):
    return LeadAssignment.objects.select_related("manager").filter(lead=lead).first()


@sync_to_async
def _create_lead_assignment(lead: TrialLead, manager: User):
    return LeadAssignment.objects.create(lead=lead, manager=manager)


@sync_to_async
def _update_lead_assignment(existing, manager: User):
    existing.manager = manager
    existing.claimed_at = timezone.now()
    existing.save(update_fields=["manager", "claimed_at"])


@sync_to_async
def _update_lead_status_contacted(lead: TrialLead):
    lead.status = TrialLead.Status.CONTACTED
    lead.save(update_fields=["status"])


@sync_to_async
def _get_lead_company_name(lead: TrialLead) -> Optional[str]:
    return lead.company_name or (lead.company.name if lead.company else None)


# ═══════════════════════════════════════════════════════════════════════
#  HOMEWORK HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_homework_submission_by_id(submission_id: int):
    return HomeworkSubmission.objects.select_related(
        "task", "student", "task__teacher"
    ).get(id=submission_id)


@sync_to_async
def _get_homework_task_title(task) -> str:
    return task.title


@sync_to_async
def _get_submission_student_name(submission) -> str:
    return (
        f"{submission.student.first_name} {submission.student.last_name}".strip()
        or str(submission.student.id)
    )


@sync_to_async
def _get_submission_task_title(submission) -> str:
    return submission.task.title


@sync_to_async
def _get_submission_task_group_name(submission) -> str:
    return submission.task.group.name if submission.task.group else "—"


# ═══════════════════════════════════════════════════════════════════════
#  TASK HELPERS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_task_by_id(task_id: int):
    return Task.objects.select_related(
        "assigned_to", "created_by", "company"
    ).get(id=task_id)


@sync_to_async
def _get_task_assigned_to_name(task: Task) -> str:
    if not task.assigned_to:
        return "—"
    return (
        f"{task.assigned_to.first_name} {task.assigned_to.last_name}".strip()
        or task.assigned_to.username
    )


@sync_to_async
def _get_task_created_by_name(task: Task) -> str:
    if not task.created_by:
        return "—"
    return (
        f"{task.created_by.first_name} {task.created_by.last_name}".strip()
        or task.created_by.username
    )


@sync_to_async
def _get_task_company_name(task: Task) -> Optional[str]:
    if task.company:
        return task.company.name
    return task.company_name or None


@sync_to_async
def _get_manager_tasks_by_status(manager: User, status: str):
    """Get tasks for a manager filtered by status."""
    return list(
        Task.objects.filter(
            assigned_to=manager,
            status=status,
        ).select_related("created_by", "company").order_by("due_date", "-priority")
    )


@sync_to_async
def _update_task_status(task_id: int, new_status: str):
    """Update a task's status."""
    Task.objects.filter(id=task_id).update(status=new_status)


@sync_to_async
def _get_task_stats_for_company(company):
    """Get task statistics for a company."""
    today = timezone.localdate()
    base_qs = Task.objects.filter(company=company)

    total = base_qs.count()
    pending = base_qs.filter(status=Task.Status.PENDING).count()
    in_progress = base_qs.filter(status=Task.Status.IN_PROGRESS).count()
    completed = base_qs.filter(status=Task.Status.COMPLETED).count()

    overdue_count = (
        base_qs.filter(due_date__lt=today)
        .exclude(status=Task.Status.COMPLETED)
        .count()
    )

    completed_tasks = list(
        base_qs.filter(status=Task.Status.COMPLETED)
        .values("completed_at", "due_date")
    )
    completed_on_time = sum(
        1 for t in completed_tasks
        if t["completed_at"] and t["completed_at"].date() <= t["due_date"]
    )
    completed_overdue = completed - completed_on_time

    high = base_qs.filter(priority=Task.Priority.HIGH).count()
    medium = base_qs.filter(priority=Task.Priority.MEDIUM).count()
    low = base_qs.filter(priority=Task.Priority.LOW).count()

    top_overdue = list(
        base_qs.filter(due_date__lt=today)
        .exclude(status=Task.Status.COMPLETED)
        .select_related("assigned_to")
        .order_by("due_date", "-priority")[:5]
    )

    managers_count = base_qs.values("assigned_to").distinct().count()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue_count,
        "completed_on_time": completed_on_time,
        "completed_overdue": completed_overdue,
        "high": high,
        "medium": medium,
        "low": low,
        "managers_count": managers_count,
        "top_overdue": top_overdue,
    }


# ═══════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

@sync_to_async
def _get_valid_bind_code(user: User, code: str) -> bool:
    """Check if a bind code is valid for the given user."""
    from django.utils import timezone
    return TelegramBindCode.objects.filter(
        user=user,
        code=code,
        is_used=False,
        expires_at__gt=timezone.now(),
    ).exists()


@sync_to_async
def _mark_bind_code_used(user: User, code: str):
    """Mark a bind code as used."""
    TelegramBindCode.objects.filter(
        user=user,
        code=code,
        is_used=False,
    ).update(is_used=True)


@sync_to_async
def _get_user_by_bind_code(code: str) -> User | None:
    """Find a user by a valid (unused, unexpired) bind code."""
    from django.utils import timezone
    code_obj = TelegramBindCode.objects.filter(
        code=code,
        is_used=False,
        expires_at__gt=timezone.now(),
    ).select_related("user").first()
    return code_obj.user if code_obj else None


def parse_schedule_days(value: str) -> set[int]:
    """Parse schedule days string into set of weekday indices (0=Monday)."""
    if not value:
        return set()
    normalized = (
        value.lower()
        .replace(".", " ")
        .replace(",", " ")
        .replace(";", " ")
        .replace("/", " ")
    )
    tokens = [token for token in normalized.split() if token]
    mapping = [
        (0, ["mon", "monday", "пн", "дүй", "дүйш"]),
        (1, ["tue", "tuesday", "вт", "шей"]),
        (2, ["wed", "wednesday", "ср", "шар"]),
        (3, ["thu", "thursday", "чт", "бей"]),
        (4, ["fri", "friday", "пт", "жум"]),
        (5, ["sat", "saturday", "сб", "иш"]),
        (6, ["sun", "sunday", "вс", "жек"]),
    ]
    result: set[int] = set()
    for token in tokens:
        for idx, keys in mapping:
            if any(token.startswith(key) for key in keys):
                result.add(idx)
                break
    return result


def get_upcoming_groups(minutes_ahead: int = 30) -> list[Group]:
    """Find active groups with a lesson starting in approximately `minutes_ahead` minutes."""
    now = timezone.localtime()
    today = now.date()
    current_weekday = now.weekday()
    current_minutes = now.hour * 60 + now.minute

    upcoming = []
    groups = Group.objects.filter(
        status=Group.Status.ACTIVE,
        start_date__lte=today,
        schedule_time__isnull=False,
    ).filter(
        Q(end_date__gte=today) | Q(end_date__isnull=True)
    ).select_related("course", "teacher", "auditorium")

    for group in groups:
        days = parse_schedule_days(group.schedule_days)
        if current_weekday not in days:
            continue

        try:
            time_str = group.schedule_time.strip()
            parts = time_str.split(":")
            lesson_minutes = int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            continue

        diff = lesson_minutes - current_minutes
        if 0 <= diff <= minutes_ahead + 5:
            upcoming.append(group)

    return upcoming
