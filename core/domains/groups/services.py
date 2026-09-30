import re
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
        for index, keys in mapping:
            if any(
                token.startswith(key)
                for key in keys
            ):
                result.add(index)
                break

    return result


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
                "Auditorium is busy at this time."
            )

        raise PermissionDenied(
            (
                f"Преподаватель «{target}» уже "
                f"занят в это время в группе "
                f"«{group.name}»."
            )
        )
