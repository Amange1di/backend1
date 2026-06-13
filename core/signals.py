"""
Signal handlers for the core app.

- trial_lead_created: Sends Telegram notification to managers when a new lead comes in
- group_teacher_assigned: Sends Telegram notification to teacher to confirm group
- homework_submission_created: Sends Telegram notification to teacher about new submission
- homework_submission_reviewed: Sends Telegram notification to student about review
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TrialLead, Group, HomeworkSubmission, HomeworkTask, Task

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async function from a sync context."""
    try:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.ensure_future(coro)
        else:
            asyncio.run(coro)
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


@receiver(post_save, sender=TrialLead)
def trial_lead_created(sender, instance, created, **kwargs):
    """Send Telegram notification when a new trial lead is created."""
    if not created:
        return

    if instance.source and instance.source.startswith("manual"):
        return

    logger.info(f"New lead created: {instance.full_name} (source: {instance.source})")

    try:
        from telegram_bot.notifications import send_lead_notification

        _run_async(send_lead_notification(instance))
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")


@receiver(post_save, sender=Group)
def group_created_or_updated(sender, instance, created, **kwargs):
    """Send Telegram notification to teacher when assigned to a new group.

    Only fires when status is 'pending' and a teacher is assigned.
    """
    if not instance.teacher:
        return

    # Check if this is a new group with pending status, or an update with status=pending
    if instance.status != Group.Status.PENDING:
        return

    # Avoid re-sending if it's an update and was already notified
    if not created:
        # For updates, only send if status changed to pending
        try:
            old = Group.objects.get(id=instance.id)
            if old.status == Group.Status.PENDING and old.teacher_id == instance.teacher_id:
                return  # Already notified
        except Group.DoesNotExist:
            pass

    logger.info(f"Group {instance.id} ({instance.name}) needs teacher confirmation")

    try:
        from telegram_bot.notifications import send_group_confirmation

        _run_async(send_group_confirmation(instance, instance.teacher))
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")


@receiver(post_save, sender=HomeworkSubmission)
def homework_submission_created(sender, instance, created, **kwargs):
    """Send Telegram notification to teacher when a student submits homework."""
    if not created:
        return

    logger.info(f"Homework submission {instance.id} by student {instance.student_id}")

    try:
        from telegram_bot.notifications import send_homework_submission_notification

        _run_async(send_homework_submission_notification(instance))
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")


@receiver(post_save, sender=Task)
def task_created_or_updated(sender, instance, created, **kwargs):
    """Send Telegram notification when a task is assigned or status changes.

    - When a task is created: notifies the assigned manager.
    - When a task status changes (by manager): notifies course admins.
    """
    if created:
        # Task created — notify the assigned manager
        if not instance.assigned_to:
            return
        if instance.assigned_to.telegram_chat_id:
            logger.info(f"Task {instance.id} assigned to manager {instance.assigned_to_id}")
            try:
                from telegram_bot.notifications import send_task_assigned_notification
                _run_async(send_task_assigned_notification(instance))
            except ImportError:
                logger.warning("telegram_bot module not available, skipping notification")
        return

    # Status changed — notify course admins
    # Only notify for meaningful status changes, not just updates to is_seen etc.
    try:
        old = Task.objects.get(id=instance.id)
        if old.status == instance.status:
            return  # Status didn't change
    except Task.DoesNotExist:
        pass

    logger.info(f"Task {instance.id} status changed to {instance.status}")
    try:
        from telegram_bot.notifications import send_task_status_changed_notification
        _run_async(send_task_status_changed_notification(instance))
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")


@receiver(post_save, sender=HomeworkSubmission)
def homework_submission_reviewed(sender, instance, created, **kwargs):
    """Send Telegram notification to student when their homework is reviewed."""
    if created:
        return

    # Only notify when status is REVIEWED or REJECTED (not just any update)
    if instance.status not in (
        HomeworkSubmission.Status.REVIEWED,
        HomeworkSubmission.Status.REJECTED,
    ):
        return

    # Check if status actually changed
    try:
        old = HomeworkSubmission.objects.get(id=instance.id)
        if old.status == instance.status:
            return
    except HomeworkSubmission.DoesNotExist:
        pass

    logger.info(f"Homework submission {instance.id} reviewed, status={instance.status}")

    try:
        from telegram_bot.notifications import send_submission_reviewed_notification

        _run_async(send_submission_reviewed_notification(instance))
    except ImportError:
        logger.warning("telegram_bot module not available, skipping notification")
