from datetime import timedelta

from django.utils import timezone

from core.models import HomeworkTask, Student


def student_can_access_task(
    task: HomeworkTask,
    student: Student,
) -> bool:
    if (
        task.target_type
        == HomeworkTask.TargetType.SPECIFIC_STUDENTS
    ):
        return task.students.filter(id=student.id).exists()

    return task.group.students.filter(id=student.id).exists()


def is_submission_locked(task: HomeworkTask) -> bool:
    if not task.hard_deadline:
        return False
    if task.allow_late:
        return False

    grace_delta = timedelta(
        minutes=task.grace_period_minutes or 0
    )
    return timezone.now() > (task.deadline + grace_delta)
