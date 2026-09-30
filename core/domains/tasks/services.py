from calendar import monthrange
from datetime import date, timedelta

from core.models import Task, User


def resolve_user_company_id(user: User):
    if getattr(user, "company_id", None):
        return user.company_id

    if (
        user.role == User.Role.MANAGER
        and user.created_by
    ):
        return getattr(
            user.created_by,
            "company_id",
            None,
        )

    return None


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(
        value.day,
        monthrange(year, month)[1],
    )
    return date(year, month, day)


def build_task_instances(validated_data, user):
    repeat_type = validated_data.get(
        "repeat_type",
        Task.RepeatType.NONE,
    )
    start_date = validated_data["due_date"]
    end_date = start_date + timedelta(days=180)
    dates = []

    if repeat_type == Task.RepeatType.DAILY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
    elif repeat_type == Task.RepeatType.WEEKLY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=7)
    elif repeat_type == Task.RepeatType.MONTHLY:
        current = start_date
        while current <= end_date:
            dates.append(current)
            current = add_months(current, 1)
    else:
        dates.append(start_date)

    return [
        Task(
            title=validated_data.get("title", ""),
            description=validated_data.get("description", ""),
            assigned_to=validated_data.get("assigned_to"),
            company=user.company,
            created_by=user,
            due_date=due_date,
            due_time=validated_data.get("due_time"),
            status=validated_data.get(
                "status",
                Task.Status.PENDING,
            ),
            priority=validated_data.get(
                "priority",
                Task.Priority.MEDIUM,
            ),
            repeat_type=repeat_type,
        )
        for due_date in dates
    ]
