import re

from django.db import models
from datetime import date, timedelta

from rest_framework.exceptions import PermissionDenied

from core.models import Group


def parse_schedule_days(value: str) -> set[int]:
    normalized = (
        value.lower()
        .replace(".", " ")
        .replace(",", " ")
        .replace(";", " ")
        .replace("/", " ")
    )
    tokens = [
        token
        for token in normalized.split()
        if token
    ]
    mapping = [
        (
            0,
            [
                "mon",
                "monday",
                "пн",
                "дүй",
                "дүйш",
            ],
        ),
        (
            1,
            [
                "tue",
                "tuesday",
                "вт",
                "шей",
            ],
        ),
        (
            2,
            [
                "wed",
                "wednesday",
                "ср",
                "шар",
            ],
        ),
        (
            3,
            [
                "thu",
                "thursday",
                "чт",
                "бей",
            ],
        ),
        (
            4,
            [
                "fri",
                "friday",
                "пт",
                "жум",
            ],
        ),
        (
            5,
            [
                "sat",
                "saturday",
                "сб",
                "иш",
            ],
        ),
        (
            6,
            [
                "sun",
                "sunday",
                "вс",
                "жек",
            ],
        ),
    ]

    result: set[int] = set()

    for token in tokens:
        if token.isdigit():
            numeric_day = int(token)
            if 0 <= numeric_day <= 6:
                result.add(numeric_day)
                continue

        for index, keys in mapping:
            if any(
                token.startswith(key)
                for key in keys
            ):
                result.add(index)
                break

    return result


def parse_working_hours(value: str):
    if not value:
        return None

    match = re.match(
        r"^\s*(\d{1,2}[:.]\d{2})\s*[-–—]\s*(\d{1,2}[:.]\d{2})\s*$",
        value,
    )
    if not match:
        return None

    start = parse_time_to_minutes(match.group(1))
    end = parse_time_to_minutes(match.group(2))
    if start is None or end is None or end <= start:
        return None

    return start, end


def parse_time_to_minutes(value: str):
    if not value:
        return None

    match = re.match(
        r"^(\d{1,2})[:.](\d{2})$",
        value.strip(),
    )
    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))

    if (
        hours < 0
        or hours > 23
        or minutes < 0
        or minutes > 59
    ):
        return None

    return hours * 60 + minutes


def ranges_overlap(
    start_a,
    end_a,
    start_b,
    end_b,
):
    a_start = start_a or date(1970, 1, 1)
    a_end = end_a or date(2999, 12, 31)
    b_start = start_b or date(1970, 1, 1)
    b_end = end_b or date(2999, 12, 31)

    return (
        a_start <= b_end
        and b_start <= a_end
    )


def time_ranges_overlap(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> bool:
    return (
        start_a < end_b
        and start_b < end_a
    )


def compute_group_end_date(
    start_date,
    schedule_days: str,
    lessons_count,
):
    if (
        not start_date
        or not lessons_count
        or not schedule_days
    ):
        return None

    days_set = parse_schedule_days(
        schedule_days
    )
    if not days_set:
        return None

    total = int(lessons_count)
    if total <= 0:
        return None

    current = start_date
    count = 0

    while count < total:
        if current.weekday() in days_set:
            count += 1
            if count == total:
                break

        current += timedelta(days=1)

    return current


GROUP_SCHEDULE_BREAK_MINUTES = 15


def ensure_group_schedule_available(
    *,
    serializer,
    instance=None,
):
    """
    Hard backend validation for a group's timetable.

    Both the selected auditorium and teacher must be free for every selected
    weekday across the group's active date range. A 15-minute turnover/break
    is enforced around each lesson.
    """
    auditorium = serializer.validated_data.get(
        "auditorium",
        instance.auditorium if instance else None,
    )
    teacher = serializer.validated_data.get(
        "teacher",
        instance.teacher if instance else None,
    )
    schedule_time = serializer.validated_data.get(
        "schedule_time",
        instance.schedule_time if instance else "",
    )
    schedule_days = serializer.validated_data.get(
        "schedule_days",
        instance.schedule_days if instance else "",
    )
    start_date = serializer.validated_data.get(
        "start_date",
        instance.start_date if instance else None,
    )
    end_date = serializer.validated_data.get(
        "end_date",
        instance.end_date if instance else None,
    )
    course = serializer.validated_data.get(
        "course",
        instance.course if instance else None,
    )
    lessons_per_month = serializer.validated_data.get(
        "lessons_per_month",
        instance.lessons_per_month if instance else None,
    )

    if not auditorium:
        raise PermissionDenied("auditorium_required")
    if not teacher:
        raise PermissionDenied("teacher_required")
    if not schedule_time:
        raise PermissionDenied("schedule_time_required")
    if not schedule_days:
        raise PermissionDenied("schedule_days_required")
    if not start_date:
        raise PermissionDenied("start_date_required")
    if not end_date:
        raise PermissionDenied("end_date_required")
    if not course:
        raise PermissionDenied("course_required")

    duration = course.lesson_duration_minutes or 0
    if duration <= 0:
        raise PermissionDenied("lesson_duration_required")

    start_minutes = parse_time_to_minutes(schedule_time)
    if start_minutes is None:
        raise PermissionDenied("schedule_time_invalid")

    days_set = parse_schedule_days(schedule_days)
    if not days_set:
        raise PermissionDenied("schedule_days_invalid")

    if lessons_per_month:
        required_weekly_days = max(
            1,
            min(7, (int(lessons_per_month) + 3) // 4),
        )
        if len(days_set) != required_weekly_days:
            raise PermissionDenied({
                "detail": "lesson_days_count_mismatch",
                "required_weekly_days": required_weekly_days,
                "selected_weekly_days": len(days_set),
                "lessons_per_month": lessons_per_month,
            })

    teacher_working_days = parse_schedule_days(
        getattr(teacher, "working_days", "") or ""
    )
    if teacher_working_days and not days_set.issubset(teacher_working_days):
        raise PermissionDenied({
            "detail": "teacher_unavailable_day",
            "teacher": str(teacher),
            "requested_days": sorted(days_set),
            "working_days": sorted(teacher_working_days),
        })

    end_minutes = start_minutes + duration

    teacher_hours = parse_working_hours(
        getattr(teacher, "working_hours", "") or ""
    )
    if teacher_hours:
        work_start, work_end = teacher_hours
        if start_minutes < work_start or end_minutes > work_end:
            raise PermissionDenied({
                "detail": "teacher_outside_working_hours",
                "teacher": str(teacher),
                "requested_start": schedule_time,
                "lesson_duration_minutes": duration,
                "working_hours": teacher.working_hours,
            })
    queryset = (
        Group.objects
        .filter(archived_at__isnull=True)
        .select_related("course", "teacher", "auditorium")
        .filter(
            models.Q(auditorium=auditorium)
            | models.Q(teacher=teacher)
        )
    )

    if instance:
        queryset = queryset.exclude(pk=instance.pk)

    for group in queryset:
        if not group.schedule_time or not group.schedule_days:
            continue

        if not ranges_overlap(
            start_date,
            end_date,
            group.start_date,
            group.end_date,
        ):
            continue

        other_days = parse_schedule_days(group.schedule_days)
        common_days = days_set.intersection(other_days)
        if not common_days:
            continue

        other_start = parse_time_to_minutes(group.schedule_time)
        if other_start is None:
            continue

        other_duration = (
            group.course.lesson_duration_minutes
            if group.course
            else 0
        ) or 0
        if other_duration <= 0:
            continue

        other_end = other_start + other_duration

        # Treat the 15-minute turnover as part of the occupied slot.
        overlaps_time = (
            start_minutes < other_end + GROUP_SCHEDULE_BREAK_MINUTES
            and other_start < end_minutes + GROUP_SCHEDULE_BREAK_MINUTES
        )
        if not overlaps_time:
            continue

        conflict = {
            "group_id": group.id,
            "group": group.name,
            "schedule_time": group.schedule_time,
            "schedule_days": group.schedule_days,
            "overlap_days": sorted(common_days),
        }

        if group.auditorium_id == auditorium.id:
            raise PermissionDenied({
                "detail": "auditorium_busy",
                "auditorium": str(auditorium),
                **conflict,
            })

        if group.teacher_id == teacher.id:
            raise PermissionDenied({
                "detail": "teacher_busy",
                "teacher": str(teacher),
                **conflict,
            })


def ensure_resource_available(

    *,
    serializer,
    instance=None,
    resource="auditorium",
):
    if resource == "auditorium":
        target = serializer.validated_data.get(
            "auditorium",
            instance.auditorium
            if instance
            else None,
        )
        filter_kwargs = {
            "auditorium": target
        }
    else:
        target = serializer.validated_data.get(
            "teacher",
            instance.teacher
            if instance
            else None,
        )
        filter_kwargs = {
            "teacher": target
        }

    if not target:
        return

    schedule_time = serializer.validated_data.get(
        "schedule_time",
        instance.schedule_time
        if instance
        else "",
    )
    schedule_days = serializer.validated_data.get(
        "schedule_days",
        instance.schedule_days
        if instance
        else "",
    )
    start_date = serializer.validated_data.get(
        "start_date",
        instance.start_date
        if instance
        else None,
    )
    end_date = serializer.validated_data.get(
        "end_date",
        instance.end_date
        if instance
        else None,
    )
    course = serializer.validated_data.get(
        "course",
        instance.course
        if instance
        else None,
    )

    if (
        not schedule_time
        or not schedule_days
        or not course
    ):
        return

    duration = (
        course.lesson_duration_minutes
        or None
    )
    if not duration:
        return

    start_minutes = parse_time_to_minutes(
        schedule_time
    )
    if start_minutes is None:
        return

    end_minutes = (
        start_minutes
        + duration
    )
    days_set = parse_schedule_days(
        schedule_days
    )
    if not days_set:
        return

    queryset = Group.objects.filter(
        **filter_kwargs
    )
    if instance:
        queryset = queryset.exclude(
            id=instance.id
        )

    for group in queryset:
        if (
            not group.schedule_time
            or not group.schedule_days
        ):
            continue

        other_duration = (
            group.course.lesson_duration_minutes
            if group.course
            else None
        )
        if not other_duration:
            continue

        other_start = parse_time_to_minutes(
            group.schedule_time
        )
        if other_start is None:
            continue

        other_end = (
            other_start
            + other_duration
        )

        if not time_ranges_overlap(
            start_minutes,
            end_minutes,
            other_start,
            other_end,
        ):
            continue

        other_days = parse_schedule_days(
            group.schedule_days
        )
        if (
            not other_days
            or not days_set.intersection(
                other_days
            )
        ):
            continue

        if not ranges_overlap(
            start_date,
            end_date,
            group.start_date,
            group.end_date,
        ):
            continue

        if resource == "auditorium":
            raise PermissionDenied(
                "auditorium_busy"
            )

        raise PermissionDenied({
            "detail": "teacher_busy",
            "teacher": str(target),
            "group": group.name,
        })
